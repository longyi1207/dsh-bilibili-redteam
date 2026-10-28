"""Host-side model calls (world generation, judging) on Azure, with retries, a cost ledger and a response cache.

These calls never go through the sandbox gateway: they are the experimenter's tools, not the agents'.
Models are chosen from a different family than the agents' model (DeepSeek V4.1 Flash) where it matters:
the judge is an OpenAI model, so it does not grade text in its own style.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import threading
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError

from .util import JsonlWriter, find_env_file, read_jsonl, utc_iso

log = logging.getLogger("llm")


@dataclass(frozen=True)
class HostModel:
    key: str
    deployment: str
    route: str               # "openai" (resource *.openai.azure.com) or "foundry" (*.services.ai.azure.com)
    price: dict              # USD per 1M tokens
    params: dict


# Prices: Azure Retail Prices API (USD per 1M tokens, global deployments, retrieved 2026-10-27).
MODELS = {
    "judge": HostModel("judge", "gpt-5.6-luna", "openai", {"input": 0.20, "cached_input": 0.02, "output": 1.20},
                       {"reasoning_effort": "low", "max_completion_tokens": 4000}),
    "writer": HostModel("writer", "DeepSeek-V4-Pro", "foundry", {"input": 1.74, "cached_input": 0.145, "output": 3.48},
                        {"max_tokens": 6000}),
}


class BudgetExceeded(RuntimeError):
    pass


class ContentFiltered(RuntimeError):
    pass


class HostLLM:
    def __init__(self, ledger: Path, cache_dir: Path, max_usd: float, concurrency: int = 8):
        path = find_env_file()
        env = dotenv_values(path) if path else {}
        key, endpoint = env.get("AZURE_OPENAI_API_KEY"), (env.get("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        if not key or not endpoint:
            raise SystemExit(f"AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT not found (env file: {path})")
        resource = endpoint.split("//")[-1].split(".")[0]
        self.clients = {"openai": AsyncOpenAI(api_key=key, base_url=f"{endpoint}/openai/v1/"),
                        "foundry": AsyncOpenAI(api_key=key, base_url=f"https://{resource}.services.ai.azure.com/openai/v1")}
        self.ledger = JsonlWriter(ledger)
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_usd = max_usd
        self.spent = sum(r.get("usd", 0.0) for r in read_jsonl(ledger))
        self._lock = threading.Lock()
        self.sem = asyncio.Semaphore(concurrency)

    async def complete(self, model_key: str, messages: list[dict], *, purpose: str, json_mode: bool = False) -> str:
        m = MODELS[model_key]
        body = {"model": m.deployment, "messages": messages, **m.params}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        digest = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        cached = self.cache_dir / f"{digest}.json"
        if cached.exists():
            return json.loads(cached.read_text())["text"]
        if self.spent >= self.max_usd:
            raise BudgetExceeded(f"host LLM spend ${self.spent:.3f} reached ${self.max_usd:.2f}")
        delay = 2.0
        for attempt in range(1, 7):
            try:
                async with self.sem:
                    resp = await self.clients[m.route].chat.completions.create(**body)
                break
            except APIStatusError as e:
                detail = e.response.text[:600] if e.response is not None else str(e)
                if e.status_code == 400 and ("content_filter" in detail or "ResponsibleAIPolicyViolation" in detail):
                    raise ContentFiltered(f"{purpose}: {detail}")
                if e.status_code not in (408, 429, 500, 502, 503, 504) or attempt == 6:
                    raise RuntimeError(f"{model_key} call for {purpose!r} failed: HTTP {e.status_code}: {detail}") from e
            except (APIConnectionError, APITimeoutError, RateLimitError):
                if attempt == 6:
                    raise
            await asyncio.sleep(delay * (0.8 + 0.4 * random.random()))
            delay = min(60, delay * 2)
        choice = resp.choices[0]
        if choice.finish_reason == "content_filter":
            raise ContentFiltered(f"{model_key}: completion filtered")
        text = choice.message.content or ""
        u = resp.usage
        cached_tok = getattr(getattr(u, "prompt_tokens_details", None), "cached_tokens", 0) or 0
        usd = ((u.prompt_tokens - cached_tok) * m.price["input"] + cached_tok * m.price["cached_input"]
               + u.completion_tokens * m.price["output"]) / 1e6
        with self._lock:
            self.spent += usd
        self.ledger.write({"ts": utc_iso(), "model": m.deployment, "purpose": purpose, "prompt_tokens": u.prompt_tokens,
                           "cached_tokens": cached_tok, "completion_tokens": u.completion_tokens, "usd": round(usd, 6)})
        cached.write_text(json.dumps({"text": text, "model": m.deployment, "purpose": purpose}, ensure_ascii=False))
        return text
