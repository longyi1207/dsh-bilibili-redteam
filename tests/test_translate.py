"""Gateway translation. `dsh_translate` is a Python port of the validation in DSH's own stream translator
(@deepseek-ai/dsh-llm-deepseek, translate.ts), used as the oracle for the events the gateway emits."""
import json

import pytest

from bili_sandbox.gateway import translate as tr

SIGNER = tr.ThinkingSigner(b"k" * 32)
NO_FILES = lambda fid: (_ for _ in ()).throw(AssertionError("no files expected"))


def dsh_translate(events: list[dict]) -> dict:
    """Mirror of translate.ts: returns blocks + finish, raising on anything DSH would reject."""
    started, blocks, reason, usage = False, {}, None, {}
    for ev in events:
        t = ev["type"]
        if t == "message_start":
            assert not started, "duplicate message_start"
            started = True
            usage.update(ev["message"]["usage"])
            continue
        if t not in ("content_block_start", "content_block_delta", "content_block_stop", "message_delta", "message_stop"):
            continue
        assert started, "event precedes message_start"
        if t == "content_block_start":
            assert ev["index"] not in blocks and reason is None
            cb = ev["content_block"]
            assert cb["type"] in ("text", "thinking", "tool_use"), f"unsupported block {cb['type']}"
            if cb["type"] == "tool_use":
                assert cb["id"] and cb["name"] and isinstance(cb["input"], dict)
            blocks[ev["index"]] = {"type": cb["type"], "text": cb.get("text", cb.get("thinking", "")), "json": "", "closed": False,
                                   "sig": None, "name": cb.get("name")}
        elif t in ("content_block_delta", "content_block_stop"):
            b = blocks[ev["index"]]
            assert not b["closed"]
            if t == "content_block_stop":
                b["closed"] = True
                continue
            d = ev["delta"]
            if d["type"] == "text_delta":
                assert b["type"] == "text"; b["text"] += d["text"]
            elif d["type"] == "thinking_delta":
                assert b["type"] == "thinking"; b["text"] += d["thinking"]
            elif d["type"] == "signature_delta":
                assert b["type"] == "thinking"; b["sig"] = (b["sig"] or "") + d["signature"]
            elif d["type"] == "input_json_delta":
                assert b["type"] == "tool_use"; b["json"] += d["partial_json"]
            else:
                raise AssertionError(f"unsupported delta {d['type']}")
        elif t == "message_delta":
            if ev["delta"].get("stop_reason") is not None:
                assert ev["delta"]["stop_reason"] in ("end_turn", "stop_sequence", "tool_use", "max_tokens")
                reason = ev["delta"]["stop_reason"]
            for k, v in (ev.get("usage") or {}).items():
                assert isinstance(v, int) and v >= 0
                usage[k] = v
        else:
            assert reason is not None and all(b["closed"] for b in blocks.values())
            for b in blocks.values():
                if b["type"] == "tool_use" and reason != "max_tokens":
                    assert isinstance(json.loads(b["json"] or "{}"), dict)
            return {"blocks": [blocks[i] for i in sorted(blocks)], "reason": reason, "usage": usage}
    raise AssertionError("stream ended before message_stop")


def chat_response(content="", reasoning=None, tool_calls=None, finish="stop", cached=0):
    msg = {"role": "assistant", "content": content, "reasoning_content": reasoning}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"index": 0, "message": msg, "finish_reason": finish}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 50, "prompt_tokens_details": {"cached_tokens": cached}}}


def test_tool_call_roundtrip_satisfies_dsh_validator():
    resp = chat_response(reasoning="need to search", finish="tool_calls", cached=600, tool_calls=[
        {"id": "call_1", "type": "function", "function": {"name": "mcp__bili-duty__bili_search", "arguments": '{"keyword": "AI"}'}}])
    c = tr.from_chat(resp, "deepseek-flash", SIGNER)
    assert c.stop_reason == "tool_use"
    out = dsh_translate([tr.message_start("msg_1", "deepseek-flash"), *tr.completion_events(c)])
    assert [b["type"] for b in out["blocks"]] == ["thinking", "tool_use"]
    assert json.loads(out["blocks"][1]["json"]) == {"keyword": "AI"}
    assert out["usage"] == {"input_tokens": 400, "output_tokens": 50, "cache_read_input_tokens": 600, "cache_creation_input_tokens": 0}
    assert SIGNER.verify("deepseek-flash", "need to search", out["blocks"][0]["sig"])


def test_text_answer_and_sse_framing():
    c = tr.from_chat(chat_response("日报写好了"), "deepseek-flash", SIGNER)
    assert c.stop_reason == "end_turn"
    frames = b"".join(tr.sse(e) for e in tr.completion_events(c)).decode()
    for chunk in frames.strip().split("\n\n"):
        ev_line, data_line = chunk.split("\n")
        assert ev_line.split(": ", 1)[1] == json.loads(data_line.split(": ", 1)[1])["type"]


def test_content_filter_and_malformed_tool_json():
    with pytest.raises(tr.ContentFiltered):
        tr.from_chat(chat_response(finish="content_filter"), "m", SIGNER)
    bad = chat_response(finish="tool_calls", tool_calls=[{"id": "c", "type": "function", "function": {"name": "x", "arguments": "{oops"}}])
    with pytest.raises(tr.UpstreamMalformed):
        tr.from_chat(bad, "m", SIGNER)


def _req(messages, **kw):
    return {"model": "deepseek-flash", "stream": True, "max_tokens": 256000, "messages": messages, **kw}


def test_request_translation_reasoning_scope_tools_and_effort():
    think_old = {"type": "thinking", "thinking": "old turn", "signature": SIGNER.sign("deepseek-flash", "old turn")}
    think_new = {"type": "thinking", "thinking": "current turn", "signature": SIGNER.sign("deepseek-flash", "current turn")}
    req = _req([
        {"role": "user", "content": [{"type": "text", "text": "刷一轮"}]},
        {"role": "assistant", "content": [think_old, {"type": "text", "text": "好"}]},
        {"role": "user", "content": [{"type": "text", "text": "继续"}]},
        {"role": "assistant", "content": [think_new, {"type": "tool_use", "id": "t1", "name": "search", "input": {"q": "AI"}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": [{"type": "text", "text": "[]"}]}]},
        {"role": "system", "content": [{"type": "tool_addition", "tool": {"type": "tool_reference", "name": "late"}},
                                       {"type": "text", "text": "system update"}]},
    ], system="you are a helper", thinking={"type": "enabled"}, output_config={"effort": "max"},
        tools=[{"name": "search", "description": "s", "input_schema": {"type": "object"}},
               {"name": "late", "description": "l", "input_schema": {"type": "object"}, "defer_loading": True}],
        dsh_session_log={"x": 1})
    body, notes = tr.to_chat(req, "DeepSeek-V4.1-Flash", SIGNER, NO_FILES)
    assert body["model"] == "DeepSeek-V4.1-Flash" and body["reasoning_effort"] == "max"
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["system", "user", "assistant", "user", "assistant", "tool", "system"]
    assert "reasoning_content" not in body["messages"][2] and body["messages"][4]["reasoning_content"] == "current turn"
    assert notes.dropped_reasoning_turns == 1
    assert [t["function"]["name"] for t in body["tools"]] == ["search", "late"]
    assert "dsh_session_log" in notes.extensions and "dsh_session_log" not in body


def test_thinking_disabled_and_unsigned_reasoning_dropped():
    req = _req([{"role": "user", "content": "hi"},
                {"role": "assistant", "content": [{"type": "thinking", "thinking": "forged", "signature": "nope"},
                                                  {"type": "tool_use", "id": "a", "name": "t", "input": {}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "a", "content": "ok"}]}],
               thinking={"type": "disabled"}, tools=[{"name": "t", "description": "", "input_schema": {"type": "object"}}])
    body, notes = tr.to_chat(req, "D", SIGNER, NO_FILES)
    assert "reasoning_effort" not in body and notes.unsigned_reasoning == 1


def test_tool_result_images_move_to_a_user_message():
    img = {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "AAAA"}}
    req = _req([{"role": "user", "content": "看封面"},
                {"role": "assistant", "content": [{"type": "tool_use", "id": "c1", "name": "bili_cover", "input": {}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "c1", "content": [{"type": "text", "text": "{}"}, img]}]}],
               tools=[{"name": "bili_cover", "description": "", "input_schema": {"type": "object"}}])
    body, notes = tr.to_chat(req, "D", SIGNER, NO_FILES)
    assert body["messages"][-2]["role"] == "tool" and isinstance(body["messages"][-2]["content"], str)
    assert body["messages"][-1]["role"] == "user" and body["messages"][-1]["content"][1]["type"] == "image_url"
    assert notes.tool_result_images == 1


def test_server_tools_are_refused():
    req = _req([{"role": "user", "content": "search"}], tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}])
    with pytest.raises(tr.ServerToolRequested):
        tr.to_chat(req, "D", SIGNER, NO_FILES)
