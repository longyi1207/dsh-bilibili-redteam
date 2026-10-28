"""`api.deepseek.com` inside the sandbox: a Messages-compatible gateway in front of Azure AI Foundry.

Every DSH process in the sandbox talks to this service as if it were DeepSeek's official API (the
harness default `https://api.deepseek.com/anthropic`, resolved here by Docker DNS). Each agent holds its
own gateway token in `~/.dsh/.credentials.yaml`, exactly where a real user keeps a DeepSeek key; the
Azure key exists only in this container's environment.

Per call the gateway:
  1. authenticates the token -> agent id;
  2. refuses with HTTP 402 "Insufficient Balance" once the run budget is spent (DeepSeek's own answer
     when an account runs dry, which DSH classifies as QUOTA);
  3. translates the request (translate.py), calls Azure with retries, translates the answer back;
  4. streams it as Messages SSE, sending keepalive comments while Azure is still thinking so DSH's
     300 s stream-idle watchdog never fires on a long reasoning turn;
  5. appends one record to `calls.jsonl` (usage, cost, latency, outcome) and writes the full request,
     upstream exchange and emitted blocks to `bodies/<agent>/<call_id>.json.gz`.
"""
from __future__ import annotations

import asyncio
import gzip
import json
import logging
import os
import random
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from aiohttp import web

from ..util import JsonlWriter, read_jsonl, utc_iso
from . import translate as tr

log = logging.getLogger("gateway")
KEEPALIVE_S = 10
# Azure answers a blocked prompt with HTTP 400 and one of these codes; "content_safety_violation" is what Prompt
# Shields ("Jailbreak") returns for DeepSeek models (seen 2026-10-28 when peer comments addressed the agents).
AZURE_SAFETY_MARKERS = ("content_filter", "ResponsibleAIPolicyViolation", "content_safety_violation")
MAX_FILE_BYTES = 500 * 1024 * 1024


@dataclass
class ModelRoute:
    name: str
    deployment: str
    listing: dict
    price: dict          # USD per 1M tokens: input, cached_input, output


@dataclass
class GatewayConfig:
    routes: dict[str, ModelRoute]
    upstream_base_url: str
    upstream_api_key: str
    attempt_timeout_s: float     # one upstream request
    deadline_s: float            # all attempts for one client call; then the client gets a retryable overloaded_error
    max_attempts: int
    max_concurrency: int
    budget_usd: float
    tokens: dict[str, str]           # gateway token -> agent id
    admin_token: str
    data_dir: Path
    signing_key: bytes


def cost_usd(route: ModelRoute, usage: dict) -> float:
    p = route.price
    return (usage.get("input_tokens", 0) * p["input"] + usage.get("cache_read_input_tokens", 0) * p["cached_input"]
            + usage.get("output_tokens", 0) * p["output"]) / 1e6


class UpstreamError(RuntimeError):
    def __init__(self, status: int | None, body: str, retryable: bool):
        super().__init__(f"upstream {status}: {body[:300]}")
        self.status, self.body, self.retryable = status, body, retryable


class FileStore:
    """Messages Files API storage, scoped per agent, persisted under data_dir/files."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def _meta_path(self, agent: str, file_id: str) -> Path:
        return self.root / agent / f"{file_id}.json"

    def put(self, agent: str, filename: str, media_type: str, data: bytes, expires_s: int) -> dict:
        file_id = "file_" + secrets.token_hex(12)
        d = self.root / agent
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{file_id}.bin").write_bytes(data)
        meta = {"id": file_id, "type": "file", "filename": filename, "mime_type": media_type, "size_bytes": len(data),
                "created_at": utc_iso(), "downloadable": False, "_expires_at": time.time() + expires_s}
        self._meta_path(agent, file_id).write_text(json.dumps(meta))
        return {k: v for k, v in meta.items() if not k.startswith("_")}

    def meta(self, agent: str, file_id: str) -> dict | None:
        p = self._meta_path(agent, file_id)
        if not p.is_file() or "/" in file_id:
            return None
        meta = json.loads(p.read_text())
        if meta["_expires_at"] < time.time():
            return None
        return meta

    def get(self, agent: str, file_id: str) -> tuple[str, bytes]:
        meta = self.meta(agent, file_id)
        if meta is None:
            raise tr.TranslationError(f"File not found: {file_id}")
        return meta["mime_type"], (self.root / agent / f"{file_id}.bin").read_bytes()

    def list(self, agent: str) -> list[dict]:
        d = self.root / agent
        metas = [json.loads(p.read_text()) for p in d.glob("*.json")] if d.exists() else []
        metas = [m for m in metas if m["_expires_at"] >= time.time()]
        metas.sort(key=lambda m: m["created_at"], reverse=True)
        return [{k: v for k, v in m.items() if not k.startswith("_")} for m in metas]

    def delete(self, agent: str, file_id: str) -> bool:
        p = self._meta_path(agent, file_id)
        if not p.is_file():
            return False
        p.unlink()
        (self.root / agent / f"{file_id}.bin").unlink(missing_ok=True)
        return True


class Gateway:
    def __init__(self, cfg: GatewayConfig):
        self.cfg = cfg
        self.signer = tr.ThinkingSigner(cfg.signing_key)
        self.files = FileStore(cfg.data_dir / "files")
        self.calls = JsonlWriter(cfg.data_dir / "calls.jsonl")
        self.events = JsonlWriter(cfg.data_dir / "events.jsonl")
        self.sem = asyncio.Semaphore(cfg.max_concurrency)
        self.spent = sum(r.get("usd", 0.0) for r in read_jsonl(cfg.data_dir / "calls.jsonl"))
        self.session: aiohttp.ClientSession | None = None
        log.info("gateway ready: %d agents, budget $%.2f, already spent $%.4f", len(cfg.tokens), cfg.budget_usd, self.spent)

    async def on_startup(self, app):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.cfg.attempt_timeout_s))

    async def on_cleanup(self, app):
        if self.session:
            await self.session.close()

    # ------------------------------------------------------------------ helpers
    def _agent(self, request) -> str | None:
        token = request.headers.get("x-api-key") or request.headers.get("x-dsh-auth-token")
        if not token and request.headers.get("Authorization", "").startswith("Bearer "):
            token = request.headers["Authorization"][7:]
        return self.cfg.tokens.get(token or "")

    def _err(self, status: int, kind: str, message: str) -> web.Response:
        return web.json_response(tr.error_body(kind, message), status=status, dumps=lambda o: json.dumps(o, ensure_ascii=False))

    def _unauthorized(self, request) -> web.Response:
        self.events.write({"ts": utc_iso(), "kind": "auth.rejected", "path": request.path, "remote": request.remote})
        return self._err(401, "authentication_error", "Authentication Fails, Your api key is invalid")

    def _write_body(self, agent: str, call_id: str, record: dict) -> None:
        d = self.cfg.data_dir / "bodies" / agent
        d.mkdir(parents=True, exist_ok=True)
        with gzip.open(d / f"{call_id}.json.gz", "wt", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)

    async def _upstream(self, body: dict) -> dict:
        url = self.cfg.upstream_base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.cfg.upstream_api_key}", "Content-Type": "application/json"}
        delay = 2.0
        started = time.monotonic()
        for attempt in range(1, self.cfg.max_attempts + 1):
            try:
                async with self.sem, self.session.post(url, json=body, headers=headers) as r:
                    text = await r.text()
                    if r.status == 200:
                        return json.loads(text)
                    if r.status == 400 and any(m in text for m in AZURE_SAFETY_MARKERS):
                        try:
                            detail = json.loads(text)
                        except ValueError:
                            detail = text
                        raise tr.ContentFiltered("prompt", detail)
                    retryable = r.status in (408, 429, 500, 502, 503, 504)
                    err = UpstreamError(r.status, text, retryable)
                    retry_after = r.headers.get("retry-after")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                err, retry_after = UpstreamError(None, f"{type(e).__name__}: {e}", True), None
            if not err.retryable or attempt == self.cfg.max_attempts:
                raise err
            if time.monotonic() - started > self.cfg.deadline_s:
                raise UpstreamError(err.status, f"deadline {self.cfg.deadline_s:.0f}s exceeded after {attempt} attempts; last: {err.body}", True)
            wait = float(retry_after) if retry_after and retry_after.replace(".", "", 1).isdigit() else delay
            wait = min(60.0, wait) * (0.8 + 0.4 * random.random())
            log.warning("upstream attempt %d/%d failed (%s); retrying in %.1fs", attempt, self.cfg.max_attempts, err, wait)
            await asyncio.sleep(wait)
            delay = min(60.0, delay * 2)
        raise AssertionError("unreachable")

    # ------------------------------------------------------------------ Messages
    async def messages(self, request: web.Request) -> web.StreamResponse:
        agent = self._agent(request)
        if agent is None:
            return self._unauthorized(request)
        call_id = f"{int(time.time() * 1000)}-{secrets.token_hex(4)}"
        t0 = time.time()
        try:
            req = await request.json()
        except ValueError:
            return self._err(400, "invalid_request_error", "request body is not valid JSON")
        model = req.get("model")
        record = {"ts": utc_iso(t0), "call_id": call_id, "agent": agent, "model": model, "stream": bool(req.get("stream")),
                  "n_messages": len(req.get("messages") or []), "n_tools": len(req.get("tools") or [])}
        # calls.jsonl is written when a call ends; this makes in-flight (or hung) calls visible.
        self.events.write({"ts": record["ts"], "kind": "call.start", "call_id": call_id, "agent": agent, "model": model,
                           "n_messages": record["n_messages"]})
        body_log = {"request": req, "headers": {k: v for k, v in request.headers.items()
                                                if k.lower() not in ("x-api-key", "x-dsh-auth-token", "authorization")}}

        def finish(outcome: str, **extra) -> None:
            record.update(outcome=outcome, latency_s=round(time.time() - t0, 3), **extra)
            self.calls.write(record)
            self._write_body(agent, call_id, body_log | {"record": record})

        route = self.cfg.routes.get(model)
        if route is None:
            finish("unknown_model")
            return self._err(400, "invalid_request_error", "Model Not Exist")
        if self.spent >= self.cfg.budget_usd:
            finish("budget_exhausted", spent_usd=round(self.spent, 4))
            log.error("budget exhausted ($%.4f >= $%.2f); refusing call from %s", self.spent, self.cfg.budget_usd, agent)
            return self._err(402, "invalid_request_error", "Insufficient Balance")
        try:
            chat_body, notes = tr.to_chat(req, route.deployment, self.signer, lambda fid: self.files.get(agent, fid))
        except tr.ServerToolRequested as e:
            finish("server_tool_rejected", error=str(e))
            return self._err(400, "invalid_request_error", str(e))
        except (tr.TranslationError, KeyError, TypeError) as e:
            finish("bad_request", error=f"{type(e).__name__}: {e}")
            return self._err(400, "invalid_request_error", str(e))
        record.update(deployment=route.deployment, effort=notes.effort, tool_updates=len(notes.tool_updates),
                      dropped_reasoning_turns=notes.dropped_reasoning_turns, unsigned_reasoning=notes.unsigned_reasoning,
                      tool_result_images=notes.tool_result_images,
                      extension_fields={k: len(json.dumps(v, ensure_ascii=False)) for k, v in notes.extensions.items()})
        body_log["upstream_request"] = chat_body | {"messages": f"<{len(chat_body['messages'])} messages, see request>"}

        msg_id = "msg_" + secrets.token_hex(12)
        stream = None
        if req.get("stream"):
            stream = web.StreamResponse(status=200, headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache",
                                                             "x-request-id": call_id})
            await stream.prepare(request)
            await stream.write(tr.sse(tr.message_start(msg_id, model)))

        task = asyncio.ensure_future(self._upstream(chat_body))
        try:
            while True:
                done, _ = await asyncio.wait({task}, timeout=KEEPALIVE_S)
                if done:
                    break
                if stream is not None:
                    await stream.write(b": keepalive\n\n")
            resp = task.result()
            body_log["upstream_response"] = resp
            completion = tr.from_chat(resp, model, self.signer)
        except tr.ContentFiltered as e:
            finish("content_filtered", where=e.where, filter_detail=e.detail)
            log.warning("content filter (%s) on call %s from %s", e.where, call_id, agent)
            return await self._fail(stream, request, 400, "invalid_request_error",
                                    f"Content Exists Risk (upstream content filter: {e.where})")
        except tr.UpstreamMalformed as e:
            finish("upstream_malformed", error=str(e))
            return await self._fail(stream, request, 500, "api_error", f"upstream returned a malformed completion: {e}")
        except UpstreamError as e:
            finish("upstream_error", status=e.status, error=e.body[:2000])
            return await self._fail(stream, request, 503 if e.retryable else 500, "overloaded_error" if e.retryable else "api_error",
                                    f"upstream error {e.status}")
        except (ConnectionResetError, asyncio.CancelledError):
            task.cancel()
            finish("client_disconnected")
            raise

        usd = cost_usd(route, completion.usage)
        self.spent += usd
        body_log["response_blocks"] = completion.blocks
        finish("ok", stop_reason=completion.stop_reason, finish_reason=completion.raw_finish, usage=completion.usage,
               usd=round(usd, 6), spent_usd=round(self.spent, 4),
               blocks=[b["type"] if b["type"] != "tool_use" else f"tool_use:{b['name']}" for b in completion.blocks])
        if stream is None:
            return web.json_response(tr.message_body(msg_id, model, completion), dumps=lambda o: json.dumps(o, ensure_ascii=False))
        for ev in tr.completion_events(completion):
            await stream.write(tr.sse(ev))
        await stream.write_eof()
        return stream

    async def _fail(self, stream, request, status: int, kind: str, message: str):
        if stream is None:
            return self._err(status, kind, message)
        await stream.write(tr.sse(tr.error_body(kind, message)))
        await stream.write_eof()
        return stream

    # ------------------------------------------------------------------ Files API
    async def files_upload(self, request):
        agent = self._agent(request)
        if agent is None:
            return self._unauthorized(request)
        form = await request.post()
        f = form.get("file")
        if not hasattr(f, "file"):
            return self._err(400, "invalid_request_error", "multipart field 'file' is required")
        data = f.file.read()
        if len(data) > MAX_FILE_BYTES:
            return self._err(413, "invalid_request_error", "file too large")
        expires = int(form.get("expires_after[seconds]") or 7 * 86400)
        meta = self.files.put(agent, f.filename or "upload", f.content_type or "application/octet-stream", data, expires)
        self.events.write({"ts": utc_iso(), "kind": "file.upload", "agent": agent, "id": meta["id"], "bytes": len(data),
                           "mime_type": meta["mime_type"]})
        return web.json_response(meta)

    async def files_list(self, request):
        agent = self._agent(request)
        if agent is None:
            return self._unauthorized(request)
        items = self.files.list(agent)
        return web.json_response({"data": items, "first_id": items[0]["id"] if items else None,
                                  "last_id": items[-1]["id"] if items else None, "has_more": False})

    async def files_get(self, request):
        agent = self._agent(request)
        if agent is None:
            return self._unauthorized(request)
        meta = self.files.meta(agent, request.match_info["file_id"])
        if meta is None:
            return self._err(404, "not_found_error", f"File not found: {request.match_info['file_id']}")
        return web.json_response({k: v for k, v in meta.items() if not k.startswith("_")})

    async def files_delete(self, request):
        agent = self._agent(request)
        if agent is None:
            return self._unauthorized(request)
        fid = request.match_info["file_id"]
        if not self.files.delete(agent, fid):
            return self._err(404, "not_found_error", f"File not found: {fid}")
        return web.json_response({"id": fid, "type": "file_deleted"})

    # ------------------------------------------------------------------ listing, other endpoints
    async def models(self, request):
        if self._agent(request) is None:
            return self._unauthorized(request)
        return web.json_response({"object": "list", "data": [
            {"id": r.name, "object": "model", "owned_by": "deepseek", **r.listing} for r in self.cfg.routes.values()]})

    async def unsupported(self, request):
        agent = self._agent(request)
        self.events.write({"ts": utc_iso(), "kind": "unsupported_endpoint", "agent": agent, "method": request.method,
                           "path": request.path})
        return self._err(404, "not_found_error", f"{request.method} {request.path} is not available in this sandbox")

    def public_app(self) -> web.Application:
        app = web.Application(client_max_size=MAX_FILE_BYTES + 1024 * 1024)
        app.on_startup.append(self.on_startup)
        app.on_cleanup.append(self.on_cleanup)
        for root in ("/anthropic/v1", "/anthropic"):
            app.router.add_post(f"{root}/messages", self.messages)
            app.router.add_post(f"{root}/files", self.files_upload)
            app.router.add_get(f"{root}/files", self.files_list)
            app.router.add_get(f"{root}/files/{{file_id}}", self.files_get)
            app.router.add_delete(f"{root}/files/{{file_id}}", self.files_delete)
        app.router.add_get("/models", self.models)
        app.router.add_get("/v1/models", self.models)
        app.router.add_route("*", "/{tail:.*}", self.unsupported)
        return app

    # ------------------------------------------------------------------ admin
    @web.middleware
    async def admin_mw(self, request, handler):
        if not secrets.compare_digest(request.headers.get("Authorization", ""), f"Bearer {self.cfg.admin_token}"):
            return web.json_response({"error": "unauthorized"}, status=401)
        return await handler(request)

    async def admin_health(self, request):
        return web.json_response({"ok": True, "spent_usd": round(self.spent, 6), "budget_usd": self.cfg.budget_usd,
                                  "agents": sorted(set(self.cfg.tokens.values()))})

    async def admin_usage(self, request):
        per: dict = {}
        for r in read_jsonl(self.cfg.data_dir / "calls.jsonl"):
            a = per.setdefault(r["agent"], {"calls": 0, "ok": 0, "usd": 0.0, "input_tokens": 0, "output_tokens": 0,
                                            "cache_read_input_tokens": 0, "outcomes": {}})
            a["calls"] += 1
            a["outcomes"][r["outcome"]] = a["outcomes"].get(r["outcome"], 0) + 1
            if r["outcome"] == "ok":
                a["ok"] += 1
                a["usd"] += r["usd"]
                for k in ("input_tokens", "output_tokens", "cache_read_input_tokens"):
                    a[k] += r["usage"].get(k, 0)
        return web.json_response({"spent_usd": round(self.spent, 6), "budget_usd": self.cfg.budget_usd, "agents": per})

    def admin_app(self) -> web.Application:
        app = web.Application(middlewares=[self.admin_mw])
        app.router.add_get("/admin/health", self.admin_health)
        app.router.add_get("/admin/usage", self.admin_usage)
        return app


def load_gateway_config(models_yaml: Path, tokens_file: Path, admin_token_file: Path, data_dir: Path,
                        budget_usd: float) -> GatewayConfig:
    import yaml
    cfg = yaml.safe_load(models_yaml.read_text())
    up = cfg["upstream"]
    key = os.environ.get(up["api_key_env"])
    if not key:
        raise SystemExit(f"{up['api_key_env']} is not set in the gateway environment")
    base = os.environ.get(up["base_url_override_env"])
    if not base:
        endpoint = os.environ.get(up["endpoint_env"], "")
        host = endpoint.split("//")[-1].split("/")[0]
        resource = host.split(".")[0]
        if not resource:
            raise SystemExit(f"cannot derive the Foundry route: set {up['endpoint_env']} or {up['base_url_override_env']}")
        base = f"https://{resource}.services.ai.azure.com/openai/v1"
    routes = {name: ModelRoute(name, m["deployment"], m["listing"], m["price_usd_per_mtok"]) for name, m in cfg["models"].items()}
    tokens = json.loads(tokens_file.read_text())
    data_dir.mkdir(parents=True, exist_ok=True)
    key_file = data_dir / "signing.key"
    if not key_file.exists():
        key_file.write_bytes(secrets.token_bytes(32))
    return GatewayConfig(routes=routes, upstream_base_url=base, upstream_api_key=key,
                         attempt_timeout_s=float(up["attempt_timeout_s"]), deadline_s=float(up["deadline_s"]),
                         max_attempts=int(up["max_attempts"]), max_concurrency=int(up["max_concurrency"]),
                         budget_usd=budget_usd, tokens=tokens, admin_token=admin_token_file.read_text().strip(),
                         data_dir=data_dir, signing_key=key_file.read_bytes())
