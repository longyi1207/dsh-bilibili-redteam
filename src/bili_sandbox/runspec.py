"""Experiment specification: which world, which agents (harness + plugin versions, settings), what budget."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .util import CONFIGS
from .world.spec import WorldSpec, load_world

# Spend guard: a run budget above $50 needs explicit approval by setting BILI_SANDBOX_APPROVED_BUDGET_USD to at least
# the run's budget (so a typo in an experiment file cannot authorise a large spend).
UNAPPROVED_BUDGET_CAP = 50.0
APPROVAL_ENV = "BILI_SANDBOX_APPROVED_BUDGET_USD"
AGENT_ID_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")


class SpecError(ValueError):
    pass


@dataclass
class AgentSpec:
    id: str
    account: str
    owner: str | None
    dsh: str
    plugin: str
    plugin_config: dict = field(default_factory=dict)
    workspace_agents_md: Path | None = None
    deepseek_key: str = "store"      # where the user put the DeepSeek key: DSH credential store | launch environment

    @property
    def image(self) -> str:
        return f"bili-sandbox-agent:dsh{self.dsh}-plugin{self.plugin}"


@dataclass
class PeerAction:
    """One scripted action by a non-agent account, executed by the orchestrator before a wave of rounds.

    type: comment               top-level comment on `video` (labelled `label` for later replies)
          reply                 reply under the comment labelled `to_label`
          reply_to_agent_comments  reply under every public agent comment from the previous wave (up to `max`)
          reply_to_peer         reply under every comment `peer` posted earlier in this wave
    Texts may use {author} (the replied-to comment's author) and {video_title}.
    """
    account: str
    waves: str                 # "1", "2", ">=2", "all"
    type: str
    text: str
    likes: int = 0
    video: str | None = None
    label: str | None = None
    to_label: str | None = None
    peer: str | None = None
    max: int = 12

    def applies(self, wave: int) -> bool:
        w = self.waves.strip()
        if w == "all":
            return True
        if w.startswith(">="):
            return wave >= int(w[2:])
        return wave == int(w)


@dataclass
class ExperimentSpec:
    name: str
    world: WorldSpec
    budget_usd: float
    round_timeout_s: int
    agents: list[AgentSpec]
    source: Path
    raw: dict
    peers: list[PeerAction] = field(default_factory=list)


def load_versions() -> dict:
    return yaml.safe_load((CONFIGS / "versions.yaml").read_text())


def load_experiment(path: Path) -> ExperimentSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if set(raw) - {"run", "agents", "peers"}:
        raise SpecError(f"{path}: unknown top-level keys {sorted(set(raw) - {'run', 'agents', 'peers'})}")
    run = raw.get("run") or {}
    unknown = set(run) - {"name", "world", "budget_usd", "round_timeout_s"}
    if unknown:
        raise SpecError(f"run: unknown keys {sorted(unknown)}")
    for k in ("name", "world", "budget_usd"):
        if k not in run:
            raise SpecError(f"run.{k} is required")
    name = str(run["name"])
    if not name or set(name) - AGENT_ID_CHARS:
        raise SpecError("run.name must be lowercase letters, digits and '-'")
    budget = float(run["budget_usd"])
    if budget <= 0:
        raise SpecError("run.budget_usd must be positive")
    if budget > UNAPPROVED_BUDGET_CAP:
        approved = float(os.environ.get(APPROVAL_ENV, "0") or 0)
        if approved < budget:
            raise SpecError(f"run.budget_usd ${budget:.2f} exceeds ${UNAPPROVED_BUDGET_CAP:.0f}; approve it explicitly by setting "
                            f"{APPROVAL_ENV}>={budget:g}")
    world = load_world((path.parent / run["world"]).resolve())

    versions = load_versions()
    agents, seen_ids, seen_accounts = [], set(), set()
    for i, a in enumerate(raw.get("agents") or []):
        where = f"agents[{i}]"
        unknown = set(a) - {"id", "account", "owner", "dsh", "plugin", "plugin_config", "workspace_agents_md", "deepseek_key"}
        if unknown:
            raise SpecError(f"{where}: unknown keys {sorted(unknown)}")
        for k in ("id", "account", "dsh", "plugin"):
            if k not in a:
                raise SpecError(f"{where}.{k} is required")
        aid = str(a["id"])
        if not aid or set(aid) - AGENT_ID_CHARS or aid in seen_ids:
            raise SpecError(f"{where}.id {aid!r} must be unique, lowercase letters, digits and '-'")
        if a["account"] not in world.users or world.users[a["account"]].role != "agent":
            raise SpecError(f"{where}.account {a['account']!r} must be a world user with role: agent")
        if a["account"] in seen_accounts:
            raise SpecError(f"{where}.account {a['account']!r} is used by two agents")
        owner = a.get("owner")
        if owner is not None and (owner not in world.users or world.users[owner].role != "owner"):
            raise SpecError(f"{where}.owner {owner!r} must be a world user with role: owner")
        if str(a["dsh"]) not in versions["dsh"]:
            raise SpecError(f"{where}.dsh {a['dsh']} is not pinned in configs/versions.yaml")
        if str(a["plugin"]) not in versions["plugin"]:
            raise SpecError(f"{where}.plugin {a['plugin']} is not pinned in configs/versions.yaml")
        md = a.get("workspace_agents_md")
        md_path = (path.parent / md).resolve() if md else None
        if md_path is not None and not md_path.is_file():
            raise SpecError(f"{where}.workspace_agents_md {md} not found")
        key_loc = str(a.get("deepseek_key", "store"))
        if key_loc not in ("store", "env"):
            raise SpecError(f"{where}.deepseek_key must be 'store' (DSH credential store) or 'env' (exported DEEPSEEK_API_KEY)")
        cfg = dict(a.get("plugin_config") or {})
        if "pythonPath" in cfg or "dshBin" in cfg or "workspace" in cfg:
            raise SpecError(f"{where}.plugin_config: pythonPath, dshBin and workspace are set by the sandbox")
        agents.append(AgentSpec(aid, a["account"], owner, str(a["dsh"]), str(a["plugin"]), cfg, md_path, key_loc))
        seen_ids.add(aid)
        seen_accounts.add(a["account"])
    if not agents:
        raise SpecError("at least one agent is required")
    peers = []
    labels: set[str] = set()
    for i, pa in enumerate(raw.get("peers") or []):
        where = f"peers[{i}]"
        if set(pa) - {"account", "actions"}:
            raise SpecError(f"{where}: unknown keys {sorted(set(pa) - {'account', 'actions'})}")
        acct = pa.get("account")
        if acct not in world.users or world.users[acct].role != "operator":
            raise SpecError(f"{where}.account {acct!r} must be a world user with role: operator")
        for j, act in enumerate(pa.get("actions") or []):
            w2 = f"{where}.actions[{j}]"
            allowed = {"waves", "type", "text", "likes", "video", "label", "to_label", "peer", "max"}
            if set(act) - allowed:
                raise SpecError(f"{w2}: unknown keys {sorted(set(act) - allowed)}")
            a = PeerAction(account=acct, waves=str(act.get("waves", "all")), type=act.get("type", ""), text=str(act.get("text", "")),
                           likes=int(act.get("likes", 0)), video=act.get("video"), label=act.get("label"),
                           to_label=act.get("to_label"), peer=act.get("peer"), max=int(act.get("max", 12)))
            if a.type not in ("comment", "reply", "reply_to_agent_comments", "reply_to_peer"):
                raise SpecError(f"{w2}.type {a.type!r} unknown")
            if not a.text.strip():
                raise SpecError(f"{w2}.text is empty")
            if not (a.waves in ("all",) or a.waves.lstrip(">=").isdigit()):
                raise SpecError(f"{w2}.waves must be N, >=N or all")
            if a.type == "comment":
                if a.video not in world.videos:
                    raise SpecError(f"{w2}.video {a.video!r} not in the world")
                if a.label:
                    if a.label in labels:
                        raise SpecError(f"{w2}.label {a.label!r} is used twice")
                    labels.add(a.label)
            if a.type == "reply" and not a.to_label:
                raise SpecError(f"{w2}: reply needs to_label")
            if a.type == "reply_to_peer" and (a.peer not in world.users or world.users[a.peer].role != "operator"):
                raise SpecError(f"{w2}.peer {a.peer!r} must be an operator account")
            peers.append(a)
    for a in peers:
        if a.type == "reply" and a.to_label not in labels:
            raise SpecError(f"reply to unknown label {a.to_label!r}")
    return ExperimentSpec(name=name, world=world, budget_usd=budget, round_timeout_s=int(run.get("round_timeout_s", 1500)),
                          agents=agents, source=path.resolve(), raw=raw, peers=peers)
