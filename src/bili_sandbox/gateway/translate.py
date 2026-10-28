"""Translate between DeepSeek's Anthropic-compatible Messages wire format (what DSH speaks) and the
OpenAI-compatible Chat Completions route of Azure AI Foundry (where the model runs).

Request side follows `WireRequest` in @deepseek-ai/dsh-llm-deepseek (wire-types.ts):
  * top-level `system`, plus `role: system` messages later in history (models declaring
    `systemPromptUpdate: in-history`) -> system messages at the same position;
  * `tool_addition` / `tool_removal` blocks and `defer_loading` tools -> the tool set that is active at
    the end of the conversation (Chat Completions has no mid-conversation tool changes);
  * `thinking` / `output_config.effort` -> `reasoning_effort` (omitted when thinking is disabled; Azure
    rejects a `thinking` field, measured 2026-10-27);
  * `thinking` blocks -> `reasoning_content` on assistant messages of the current turn only. DeepSeek drops
    reasoning from earlier turns, and keeps it within a tool-call loop;
  * images in tool results -> a user message right after the tool messages (tool messages carry text only).

Response side produces the event sequence that DSH's translator (translate.ts) validates: one
message_start, then per block content_block_start / *_delta / content_block_stop, then message_delta
with the stop reason and cumulative usage, then message_stop.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, field

KNOWN_TOP_LEVEL = {"model", "stream", "max_tokens", "messages", "system", "thinking", "output_config",
                   "temperature", "stop_sequences", "tools", "tool_choice", "metadata", "top_p", "top_k"}
EFFORTS = {"low", "high", "max"}


class TranslationError(ValueError):
    """The client request cannot be served; answered as invalid_request_error."""


class UpstreamMalformed(RuntimeError):
    """The upstream answer cannot be expressed as a valid Messages response; answered as a retryable api_error."""


class ContentFiltered(RuntimeError):
    """Azure's content filter blocked the prompt or the completion. Recorded as its own outcome."""

    def __init__(self, where: str, detail: object):
        super().__init__(f"content filter ({where})")
        self.where = where
        self.detail = detail


class ServerToolRequested(TranslationError):
    """A server-side tool (DeepSeek native web search) was requested; the sandbox has no internet."""


class ThinkingSigner:
    """Signs reasoning text handed to the client so replayed thinking blocks can be checked."""

    def __init__(self, key: bytes):
        self.key = key

    def sign(self, model: str, text: str) -> str:
        mac = hmac.new(self.key, f"{model}\0{text}".encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).decode().rstrip("=")

    def verify(self, model: str, text: str, signature: str | None) -> bool:
        return signature is not None and hmac.compare_digest(self.sign(model, text), signature)


@dataclass
class Notes:
    """What the translation did, recorded with each call."""
    extensions: dict = field(default_factory=dict)
    tool_updates: list = field(default_factory=list)
    dropped_reasoning_turns: int = 0
    unsigned_reasoning: int = 0
    tool_result_images: int = 0
    effort: str | None = None


def _text_of(parts: list) -> str:
    return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text")


def _image_part(block: dict, resolve_file) -> dict:
    src = block.get("source") or {}
    if src.get("type") == "base64":
        return {"type": "image_url", "image_url": {"url": f"data:{src['media_type']};base64,{src['data']}"}}
    if src.get("type") == "file":
        media_type, data = resolve_file(src["file_id"])
        return {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{base64.b64encode(data).decode()}"}}
    raise TranslationError(f"unsupported image source {src.get('type')!r}")


def _blocks(content) -> list[dict]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if not isinstance(content, list):
        raise TranslationError("message content must be a string or a list of blocks")
    return content


def to_chat(req: dict, deployment: str, signer: ThinkingSigner, resolve_file) -> tuple[dict, Notes]:
    notes = Notes(extensions={k: v for k, v in req.items() if k not in KNOWN_TOP_LEVEL})
    model = req.get("model")
    if not isinstance(model, str) or not model:
        raise TranslationError("model is required")
    max_tokens = req.get("max_tokens")
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        raise TranslationError("max_tokens must be a positive integer")
    messages = req.get("messages")
    if not isinstance(messages, list) or not messages:
        raise TranslationError("messages must be a non-empty list")

    tools_raw = req.get("tools") or []
    defs, active = {}, []
    for t in tools_raw:
        if "type" in t and t.get("type") not in (None, "custom"):
            raise ServerToolRequested(f"server tool {t.get('type')!r} is not available in this sandbox (no internet)")
        defs[t["name"]] = t
        if not t.get("defer_loading"):
            active.append(t["name"])

    # Reasoning is replayed only for assistant messages after the last real user turn.
    last_user_turn = -1
    for i, m in enumerate(messages):
        if m.get("role") == "user" and any(b.get("type") in ("text", "image") for b in _blocks(m.get("content"))):
            last_user_turn = i

    out: list[dict] = []
    if req.get("system"):
        sys_text = req["system"] if isinstance(req["system"], str) else _text_of(req["system"])
        out.append({"role": "system", "content": sys_text})

    for i, m in enumerate(messages):
        role, blocks = m.get("role"), _blocks(m.get("content"))
        if role == "system":
            texts = []
            for b in blocks:
                if b.get("type") == "text":
                    texts.append(b["text"])
                elif b.get("type") in ("tool_addition", "tool_removal"):
                    name = (b.get("tool") or {}).get("name")
                    if name not in defs:
                        raise TranslationError(f"{b['type']} references undeclared tool {name!r}")
                    if b["type"] == "tool_addition" and name not in active:
                        active.append(name)
                    elif b["type"] == "tool_removal" and name in active:
                        active.remove(name)
                    notes.tool_updates.append({"message": i, "op": b["type"], "tool": name})
                else:
                    raise TranslationError(f"unsupported block {b.get('type')!r} in a system message")
            if texts:
                out.append({"role": "system", "content": "\n".join(texts)})
        elif role == "user":
            images_from_tools, user_parts = [], []
            for b in blocks:
                kind = b.get("type")
                if kind == "tool_result":
                    parts = _blocks(b.get("content") or [])
                    text = _text_of(parts)
                    imgs = [p for p in parts if p.get("type") == "image"]
                    if imgs:
                        text = (text + "\n" if text else "") + f"[{len(imgs)} image(s) returned; shown in the next message]"
                        images_from_tools.append((b["tool_use_id"], imgs))
                        notes.tool_result_images += len(imgs)
                    if b.get("is_error"):
                        text = "[tool error] " + text
                    out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": text})
                elif kind == "text":
                    user_parts.append({"type": "text", "text": b["text"]})
                elif kind == "image":
                    user_parts.append(_image_part(b, resolve_file))
                elif kind in ("tool_addition", "tool_removal"):
                    raise TranslationError(f"{kind} is only valid in a system message")
                else:
                    raise TranslationError(f"unsupported block {kind!r} in a user message")
            for tool_id, imgs in images_from_tools:
                out.append({"role": "user", "content": [{"type": "text", "text": f"[images returned by tool call {tool_id}]"}]
                            + [_image_part(p, resolve_file) for p in imgs]})
            if user_parts:
                content = user_parts[0]["text"] if len(user_parts) == 1 and user_parts[0]["type"] == "text" else user_parts
                out.append({"role": "user", "content": content})
        elif role == "assistant":
            texts, calls, reasoning = [], [], []
            for b in blocks:
                kind = b.get("type")
                if kind == "text":
                    texts.append(b["text"])
                elif kind == "thinking":
                    if not signer.verify(model, b.get("thinking", ""), b.get("signature")):
                        notes.unsigned_reasoning += 1
                        continue
                    reasoning.append(b["thinking"])
                elif kind == "tool_use":
                    calls.append({"id": b["id"], "type": "function",
                                  "function": {"name": b["name"], "arguments": json.dumps(b.get("input") or {}, ensure_ascii=False)}})
                else:
                    raise TranslationError(f"unsupported block {kind!r} in an assistant message")
            msg: dict = {"role": "assistant", "content": "".join(texts)}
            if calls:
                msg["tool_calls"] = calls
            if reasoning:
                if i > last_user_turn:
                    msg["reasoning_content"] = "".join(reasoning)
                else:
                    notes.dropped_reasoning_turns += 1
            out.append(msg)
        else:
            raise TranslationError(f"unsupported role {role!r}")

    body: dict = {"model": deployment, "messages": out, "max_tokens": max_tokens, "stream": False}
    tools = [{"type": "function", "function": {"name": n, "description": defs[n].get("description", ""),
                                               "parameters": defs[n].get("input_schema") or {"type": "object"}}}
             for n in active]
    if tools:
        body["tools"] = tools
        tc = req.get("tool_choice")
        if tc:
            body["tool_choice"] = {"auto": "auto", "any": "required", "none": "none"}.get(tc.get("type"), "auto") \
                if tc.get("type") != "tool" else {"type": "function", "function": {"name": tc["name"]}}
    thinking = (req.get("thinking") or {}).get("type", "enabled")
    effort = (req.get("output_config") or {}).get("effort")
    if thinking == "enabled":
        effort = effort or "high"
        if effort not in EFFORTS:
            raise TranslationError(f"unsupported effort {effort!r}")
        body["reasoning_effort"] = effort
        notes.effort = effort
    elif thinking != "disabled":
        raise TranslationError(f"thinking.type must be enabled or disabled, got {thinking!r}")
    if req.get("temperature") is not None:
        body["temperature"] = req["temperature"]
    if req.get("top_p") is not None:
        body["top_p"] = req["top_p"]
    if req.get("stop_sequences"):
        body["stop"] = list(req["stop_sequences"])
    return body, notes


@dataclass
class Completion:
    blocks: list[dict]
    stop_reason: str
    usage: dict
    raw_finish: str


def from_chat(resp: dict, model: str, signer: ThinkingSigner) -> Completion:
    try:
        choice = resp["choices"][0]
        msg = choice["message"]
    except (KeyError, IndexError, TypeError):
        raise UpstreamMalformed("response has no choices[0].message")
    finish = choice.get("finish_reason")
    if finish == "content_filter":
        raise ContentFiltered("completion", choice.get("content_filter_results") or resp.get("prompt_filter_results"))
    blocks: list[dict] = []
    reasoning = msg.get("reasoning_content")
    if reasoning:
        blocks.append({"type": "thinking", "thinking": reasoning, "signature": signer.sign(model, reasoning)})
    if msg.get("content"):
        blocks.append({"type": "text", "text": msg["content"]})
    for call in msg.get("tool_calls") or []:
        fn = call.get("function") or {}
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except ValueError:
            if finish == "length":
                args = {}
            else:
                raise UpstreamMalformed(f"tool call {fn.get('name')!r} has invalid JSON arguments")
        if not isinstance(args, dict):
            raise UpstreamMalformed(f"tool call {fn.get('name')!r} arguments are not an object")
        if not call.get("id") or not fn.get("name"):
            raise UpstreamMalformed("tool call without id or name")
        blocks.append({"type": "tool_use", "id": call["id"], "name": fn["name"], "input": args})
    has_calls = any(b["type"] == "tool_use" for b in blocks)
    if finish == "length":
        stop = "max_tokens"
    elif finish in ("tool_calls", "stop") and has_calls:
        stop = "tool_use"
    elif finish == "stop":
        stop = "end_turn"
    else:
        raise UpstreamMalformed(f"unexpected finish_reason {finish!r} (tool calls: {has_calls})")
    u = resp.get("usage") or {}
    cached = ((u.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0
    usage = {"input_tokens": max(0, int(u.get("prompt_tokens", 0)) - cached), "output_tokens": int(u.get("completion_tokens", 0)),
             "cache_read_input_tokens": cached, "cache_creation_input_tokens": 0}
    return Completion(blocks, stop, usage, finish)


def sse(event: dict) -> bytes:
    return f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n".encode()


def message_start(msg_id: str, model: str) -> dict:
    return {"type": "message_start", "message": {"id": msg_id, "type": "message", "role": "assistant", "model": model,
                                                  "content": [], "stop_reason": None, "stop_sequence": None,
                                                  "usage": {"input_tokens": 0, "output_tokens": 0}}}


def completion_events(c: Completion) -> list[dict]:
    events = []
    for i, b in enumerate(c.blocks):
        if b["type"] == "text":
            events += [{"type": "content_block_start", "index": i, "content_block": {"type": "text", "text": ""}},
                       {"type": "content_block_delta", "index": i, "delta": {"type": "text_delta", "text": b["text"]}}]
        elif b["type"] == "thinking":
            events += [{"type": "content_block_start", "index": i, "content_block": {"type": "thinking", "thinking": ""}},
                       {"type": "content_block_delta", "index": i, "delta": {"type": "thinking_delta", "thinking": b["thinking"]}},
                       {"type": "content_block_delta", "index": i, "delta": {"type": "signature_delta", "signature": b["signature"]}}]
        elif b["type"] == "tool_use":
            events += [{"type": "content_block_start", "index": i,
                        "content_block": {"type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}},
                       {"type": "content_block_delta", "index": i,
                        "delta": {"type": "input_json_delta", "partial_json": json.dumps(b["input"], ensure_ascii=False)}}]
        events.append({"type": "content_block_stop", "index": i})
    events.append({"type": "message_delta", "delta": {"stop_reason": c.stop_reason, "stop_sequence": None}, "usage": c.usage})
    events.append({"type": "message_stop"})
    return events


def message_body(msg_id: str, model: str, c: Completion) -> dict:
    """Non-streaming response (stream: false)."""
    return {"id": msg_id, "type": "message", "role": "assistant", "model": model, "content": c.blocks,
            "stop_reason": c.stop_reason, "stop_sequence": None, "usage": c.usage}


def error_body(kind: str, message: str) -> dict:
    return {"type": "error", "error": {"type": kind, "message": message}}
