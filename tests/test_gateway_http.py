"""Gateway HTTP layer against a fake Azure upstream."""
import base64
import json

import pytest
from aiohttp import FormData, web
from aiohttp.test_utils import TestClient, TestServer

from bili_sandbox.gateway.app import Gateway, GatewayConfig, ModelRoute
from bili_sandbox.util import read_jsonl

from test_translate import dsh_translate

PRICE = {"input": 0.30, "cached_input": 0.006, "output": 1.20}


def parse_sse(text: str) -> list[dict]:
    events = []
    for chunk in text.split("\n\n"):
        data = [ln[6:] for ln in chunk.split("\n") if ln.startswith("data: ")]
        if data:
            events.append(json.loads(data[0]))
    return events


@pytest.fixture
async def gw(tmp_path):
    seen = []
    mode = {"answer": "tool"}

    async def upstream(request):
        body = await request.json()
        seen.append(body)
        if mode["answer"] == "filter":
            return web.json_response({"error": {"code": "content_filter", "message": "filtered"}}, status=400)
        if mode["answer"] == "shield":
            return web.json_response({"error": {"code": "content_safety_violation",
                                                "message": "Response content blocked by label 'Jailbreak'."}}, status=400)
        msg = {"role": "assistant", "content": "", "reasoning_content": "think",
               "tool_calls": [{"id": "call_9", "type": "function", "function": {"name": "bili_search", "arguments": '{"keyword":"AI"}'}}]}
        return web.json_response({"choices": [{"message": msg, "finish_reason": "tool_calls"}],
                                  "usage": {"prompt_tokens": 2_000_000, "completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 0}}})

    up = web.Application()
    up.router.add_post("/openai/v1/chat/completions", upstream)
    up_server = TestServer(up)
    await up_server.start_server()
    cfg = GatewayConfig(routes={"deepseek-flash": ModelRoute("deepseek-flash", "DeepSeek-V4.1-Flash", {"context_window": 1}, PRICE)},
                        upstream_base_url=str(up_server.make_url("/openai/v1")), upstream_api_key="azure-key", attempt_timeout_s=30, deadline_s=60,
                        max_attempts=2, max_concurrency=4, budget_usd=0.5, tokens={"sk-a": "fish-a"}, admin_token="adm",
                        data_dir=tmp_path, signing_key=b"s" * 32)
    gateway = Gateway(cfg)
    client = TestClient(TestServer(gateway.public_app()))
    await client.start_server()
    yield client, seen, mode, tmp_path
    await client.close()
    await up_server.close()


REQ = {"model": "deepseek-flash", "stream": True, "max_tokens": 1000, "thinking": {"type": "enabled"},
       "messages": [{"role": "user", "content": [{"type": "text", "text": "刷一轮"}]}],
       "tools": [{"name": "bili_search", "description": "", "input_schema": {"type": "object"}}]}


async def test_auth_and_listing(gw):
    client, *_ = gw
    assert (await client.post("/anthropic/v1/messages", json=REQ)).status == 401
    r = await client.get("/models", headers={"x-api-key": "sk-a"})
    assert r.status == 200 and (await r.json())["data"][0]["id"] == "deepseek-flash"


async def test_stream_then_budget_stop(gw):
    client, seen, mode, data = gw
    r = await client.post("/anthropic/v1/messages", json=REQ, headers={"x-api-key": "sk-a"})
    out = dsh_translate(parse_sse(await r.text()))
    assert out["reason"] == "tool_use" and out["blocks"][1]["name"] == "bili_search"
    assert seen[0]["model"] == "DeepSeek-V4.1-Flash" and seen[0]["reasoning_effort"] == "high"
    # 2M input tokens at $0.30/M = $0.60 > budget 0.50 -> next call refused like an empty DeepSeek account
    r2 = await client.post("/anthropic/v1/messages", json=REQ, headers={"x-api-key": "sk-a"})
    assert r2.status == 402 and (await r2.json())["error"]["message"] == "Insufficient Balance"
    outcomes = [c["outcome"] for c in read_jsonl(data / "calls.jsonl")]
    assert outcomes == ["ok", "budget_exhausted"]
    assert (data / "bodies" / "fish-a").is_dir()


@pytest.mark.parametrize("answer", ["filter", "shield"])
async def test_content_filter_is_its_own_outcome(gw, answer):
    client, seen, mode, data = gw
    mode["answer"] = answer
    r = await client.post("/anthropic/v1/messages", json=REQ, headers={"x-api-key": "sk-a"})
    events = parse_sse(await r.text())
    assert events[-1]["type"] == "error" and events[-1]["error"]["type"] == "invalid_request_error"
    assert read_jsonl(data / "calls.jsonl")[-1]["outcome"] == "content_filtered"


async def test_files_api_roundtrip_and_image_reference(gw):
    client, seen, mode, data = gw
    form = FormData()
    form.add_field("file", b"\x89PNG fake", filename="cover.png", content_type="image/png")
    form.add_field("expires_after[anchor]", "created_at")
    form.add_field("expires_after[seconds]", "3600")
    meta = await (await client.post("/anthropic/v1/files", data=form, headers={"x-api-key": "sk-a"})).json()
    assert meta["type"] == "file" and meta["size_bytes"] == len(b"\x89PNG fake") and meta["filename"] == "cover.png"
    listing = await (await client.get("/anthropic/v1/files", headers={"x-api-key": "sk-a"})).json()
    assert listing["data"][0]["id"] == meta["id"] and listing["has_more"] is False
    req = json.loads(json.dumps(REQ))
    req["messages"][0]["content"].append({"type": "image", "source": {"type": "file", "file_id": meta["id"]}})
    r = await client.post("/anthropic/v1/messages", json=req, headers={"x-api-key": "sk-a"})
    assert dsh_translate(parse_sse(await r.text()))["reason"] == "tool_use"
    url = seen[-1]["messages"][-1]["content"][1]["image_url"]["url"]
    assert url == "data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()
    d = await (await client.delete(f"/anthropic/v1/files/{meta['id']}", headers={"x-api-key": "sk-a"})).json()
    assert d == {"id": meta["id"], "type": "file_deleted"}


async def test_web_search_refused(gw):
    client, seen, mode, data = gw
    req = dict(REQ, tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2}])
    r = await client.post("/anthropic/v1/messages", json=req, headers={"x-api-key": "sk-a"})
    assert r.status == 400 and not seen
    assert read_jsonl(data / "calls.jsonl")[-1]["outcome"] == "server_tool_rejected"


async def test_hung_upstream_ends_in_retryable_error(tmp_path):
    import asyncio

    async def hang(request):
        await asyncio.sleep(30)
        return web.json_response({})

    up = web.Application()
    up.router.add_post("/openai/v1/chat/completions", hang)
    up_server = TestServer(up)
    await up_server.start_server()
    cfg = GatewayConfig(routes={"deepseek-flash": ModelRoute("deepseek-flash", "D", {}, PRICE)},
                        upstream_base_url=str(up_server.make_url("/openai/v1")), upstream_api_key="k", attempt_timeout_s=0.5,
                        deadline_s=1.0, max_attempts=5, max_concurrency=4, budget_usd=1, tokens={"sk-a": "fish-a"},
                        admin_token="adm", data_dir=tmp_path, signing_key=b"s" * 32)
    client = TestClient(TestServer(Gateway(cfg).public_app()))
    await client.start_server()
    try:
        r = await client.post("/anthropic/v1/messages", json=REQ, headers={"x-api-key": "sk-a"})
        events = parse_sse(await r.text())
        assert events[0]["type"] == "message_start" and events[-1]["error"]["type"] == "overloaded_error"
        assert read_jsonl(tmp_path / "calls.jsonl")[-1]["outcome"] == "upstream_error"
        assert [e["kind"] for e in read_jsonl(tmp_path / "events.jsonl")] == ["call.start"]
    finally:
        await client.close()
        await up_server.close()
