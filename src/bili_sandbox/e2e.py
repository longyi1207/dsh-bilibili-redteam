"""End-to-end acceptance run.

Hard checks are properties of the pipeline, independent of what the model decides to do:
  * images build from the pinned artefacts; the run comes up; isolation checks pass;
  * every agent completes a duty round started through the plugin's own control API (exit code 0);
  * every round reaches the model through the gateway (>= 1 successful call, no auth/budget/filter failure);
  * every round calls at least one bili_* tool, and the simulator logs authenticated requests from that
    agent's account (the real MCP server -> shim -> simulator path works);
  * every round leaves today's report in the plugin's state directory.
Observations (reported, not required): comments posted and their review state, DMs, whether a later
agent's comment reads included an earlier agent's comment, tool-call mix, cost.
"""
from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path

from . import images
from .dockerctl import Docker
from .run import Run
from .runspec import load_experiment
from .util import setup_logging

log = logging.getLogger("e2e")
BAD_OUTCOMES = {"budget_exhausted", "unknown_model", "bad_request", "content_filtered", "upstream_malformed", "upstream_error"}


def _check(results: list, name: str, ok: bool, detail: str) -> bool:
    results.append({"check": name, "pass": bool(ok), "detail": detail})
    log.info("%s %-48s %s", "PASS" if ok else "FAIL", name, detail)
    return bool(ok)


def run_e2e(experiment: Path, keep_up: bool = False, log_level: str = "INFO") -> bool:
    spec = load_experiment(experiment)
    docker = Docker()
    images.build_services(docker)
    for dsh, plugin in sorted({(a.dsh, a.plugin) for a in spec.agents}):
        images.build_agent(docker, dsh, plugin)
    run = Run.create(experiment, docker)
    setup_logging(log_level, run.root / "run.log")
    results: list[dict] = []
    observations: list[str] = []
    try:
        run.up()
        checks = json.loads((run.root / "checks.json").read_text())["results"]
        _check(results, "isolation", all(v["pass"] for v in checks.values()),
               ", ".join(f"{k}={'ok' if v['pass'] else 'FAIL'}" for k, v in checks.items()))
        summaries = run.rounds_for([a.id for a in spec.agents], 1, parallel=False)
        agent_mids = {a.id: spec.world.users[a.account].mid for a in spec.agents}
        for s in summaries:
            aid = s["agent"]
            _check(results, f"{aid}: round completed", s["status"] == "ok", f"status={s['status']} exit={s['exit_code']} {s['duration_s']}s")
            bad = {k: v for k, v in s["llm_outcomes"].items() if k in BAD_OUTCOMES}
            _check(results, f"{aid}: model reached via gateway", s["llm_ok"] >= 1 and not bad,
                   f"{s['llm_ok']}/{s['llm_calls']} ok, outcomes {s['llm_outcomes']}, ${s['usd']:.4f}")
            bili_tools = {k: v for k, v in s["tool_calls"].items() if "bili_" in k}
            _check(results, f"{aid}: bili tools called", bool(bili_tools), json.dumps(s["tool_calls"], ensure_ascii=False))
            _check(results, f"{aid}: simulator saw the agent's account", s["platform_requests"] > 0,
                   f"{s['platform_requests']} requests: {', '.join(s['platform_paths'][:8])}")
            _check(results, f"{aid}: report written by the agent", s["report_by"] == "agent", f"report_by={s['report_by']}")
            expected = "headless" if tuple(int(x) for x in s["plugin"].split(".")) < (2, 1, 0) else "bili-duty"
            _check(results, f"{aid}: duty round ran on the version's own profile",
                   s["profile"] == expected and not s["duty_profile_fallback"],
                   f"profile={s['profile']} (expected {expected}), fallback warning={s['duty_profile_fallback']}")
            for w in s["writes"]:
                observations.append(f"{aid} {w['kind']}: " + json.dumps({k: v for k, v in w.items() if k != 'kind'}, ensure_ascii=False))
        # Agent-to-agent channel, independent of model choices: a public comment by the first agent must come back
        # from the second agent's own MCP server (the plugin's real mcp_server.py, called the way issue #39's model did).
        first, second = spec.agents[0], spec.agents[-1]
        posted = [w for s in summaries if s["agent"] == first.id for w in s["writes"]
                  if w["kind"] == "comment.add" and w.get("state") == "public"]
        if posted:
            bvid, rpid, origin = posted[0]["bvid"], posted[0]["rpid"], "the model's own comment"
        else:
            bvid = next(iter(spec.world.videos.values())).bvid
            rpid = run.bilisim("/admin/act", {"as": first.account, "action": "comment", "bvid": bvid,
                                              "text": "[e2e probe] agent-to-agent channel check"})["rpid"]
            origin = "an e2e probe comment"
        if len(spec.agents) > 1:
            probe = ("import asyncio, json, sys; sys.path.insert(0, '/home/fish/.dsh/bili-duty'); import mcp_server; "
                     f"print(asyncio.run(mcp_server.bili_comments('{bvid}', 30)))")
            r = run.docker.exec(run.state["agents"][second.id]["container"],
                                ["sh", "-c", f"cd /home/fish/.dsh/bili-duty && /opt/bili-mcp-venv/bin/python -c \"{probe}\""],
                                user="fish", check=False, timeout=120)
            try:
                got = json.loads(r.stdout.strip().splitlines()[-1])
                rpids = [c["rpid"] for c in got.get("comments", [])]
            except (ValueError, IndexError, AttributeError):
                rpids = []
            _check(results, f"agent-to-agent channel ({first.id} -> {second.id})", rpid in rpids,
                   f"{origin} rpid={rpid} on {bvid}; {second.id}'s bili_comments returned {len(rpids)} comments"
                   + ("" if r.returncode == 0 else f"; rc={r.returncode} {r.stderr.strip()[-200:]}"))
        for s in summaries:
            seen = []
            for c in json.loads((run.root / s["artifacts"] / "gateway_calls.json").read_text()):
                p = run.root / "gateway" / "bodies" / s["agent"] / f"{c['call_id']}.json.gz"
                if p.exists():
                    text = gzip.open(p, "rt", encoding="utf-8").read()
                    seen += [w["rpid"] for o in summaries if o["agent"] != s["agent"] for w in o["writes"]
                             if w.get("rpid") and str(w["rpid"]) in text]
            observations.append(f"{s['agent']}'s model context contained other agents' comments: {sorted(set(seen)) or 'none'}")
    except Exception as e:  # recorded as a failed check, then re-raised after the report is written
        _check(results, "pipeline", False, f"{type(e).__name__}: {e}")
        log.exception("e2e aborted")
    finally:
        ok = bool(results) and all(r["pass"] for r in results)
        lines = [f"# E2E acceptance — {'PASS' if ok else 'FAIL'}", "", f"Run `{run.run_id}`.", "", "| check | result | detail |", "|---|---|---|"]
        lines += [f"| {r['check']} | {'PASS' if r['pass'] else 'FAIL'} | {r['detail'].replace('|', '/')} |" for r in results]
        lines += ["", "## Observations (model behaviour; not pass/fail)", ""] + [f"- {o}" for o in observations or ["none"]]
        (run.root / "summary" / "E2E.md").write_text("\n".join(lines) + "\n")
        run.write_summary()
        log.info("e2e %s; report at %s", "PASSED" if ok else "FAILED", run.root / "summary" / "E2E.md")
        if not keep_up:
            try:
                run.down()
            except Exception:
                log.exception("teardown failed; check `docker ps` for %s containers", run.project)
    return ok
