"""World specification: the accounts, videos and conversations a run starts from.

A world file is YAML. Every entity is addressed by a human-readable `handle`; numeric Bilibili ids
(mid, aid/bvid, cid, rpid) are derived deterministically from the world seed so two runs of the same
world see identical ids. Times are offsets relative to the moment the world is seeded
(`-2d`, `-3h`, `-15m`), because the plugin itself works on real wall-clock time (Beijing windows,
"today's report").

Validation is strict: unknown keys, dangling handles, and malformed subtitles fail at load time.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .ids import av2bv

_OFFSET_RE = re.compile(r"^-?(\d+(?:\.\d+)?)([smhd])$")
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class WorldSpecError(ValueError):
    pass


def parse_offset(value: str | int | float) -> int:
    """'-2d' -> -172800. Bare numbers are seconds. Offsets must not lie in the future."""
    if isinstance(value, (int, float)):
        secs = int(value)
    else:
        m = _OFFSET_RE.match(str(value).strip())
        if not m:
            raise WorldSpecError(f"bad time offset {value!r}; use e.g. -2d, -3h, -15m, -30s")
        secs = -int(float(m.group(1)) * _UNITS[m.group(2)])
    if secs > 0:
        raise WorldSpecError(f"time offset {value!r} is in the future")
    return secs


def _check_keys(where: str, obj: dict, allowed: set[str], required: set[str] = frozenset()) -> None:
    if not isinstance(obj, dict):
        raise WorldSpecError(f"{where}: expected a mapping, got {type(obj).__name__}")
    unknown = set(obj) - allowed
    if unknown:
        raise WorldSpecError(f"{where}: unknown keys {sorted(unknown)}; allowed {sorted(allowed)}")
    missing = set(required) - set(obj)
    if missing:
        raise WorldSpecError(f"{where}: missing keys {sorted(missing)}")


@dataclass
class UserSpec:
    handle: str
    name: str
    mid: int
    sign: str = ""
    level: int = 4
    fans: int = 0
    interests: list[str] = field(default_factory=list)
    role: str = "human"          # human | agent | owner | operator
    follows: list[str] = field(default_factory=list)


@dataclass
class CommentSpec:
    by: str
    text: str
    like: int = 0
    at: int = -3600              # seconds relative to seed time
    replies: list["CommentSpec"] = field(default_factory=list)


@dataclass
class SubtitleLine:
    start: float
    end: float
    text: str


@dataclass
class DanmakuSpec:
    t: float
    text: str
    by: str | None = None


@dataclass
class VideoSpec:
    handle: str
    title: str
    owner: str
    aid: int
    bvid: str
    cid: int
    desc: str = ""
    tags: list[str] = field(default_factory=list)
    tid: int = 201
    tname: str = "科学科普"
    duration: int = 300
    published: int = -86400
    stat: dict = field(default_factory=dict)
    subtitle_kind: str = "ai"    # ai | cc | none
    subtitles: list[SubtitleLine] = field(default_factory=list)
    danmaku: list[DanmakuSpec] = field(default_factory=list)
    comments: list[CommentSpec] = field(default_factory=list)
    cover: str | None = None      # path relative to the world file; rendered from the title when absent


@dataclass
class Policy:
    """Platform risk-control rules. Defaults follow behaviour documented by plugin users (see README)."""
    review_below_level: int = 2          # comments from accounts below this level wait in review (not public)
    dm_max_chars: int = 500              # longer DMs are rejected with code 21007 (duty.md, measured by users)
    dm_stranger_max_unanswered: int = 1  # without a mutual follow, at most this many DMs until the other side replies
    read_rate_per_min: int = 120         # per account; above it the platform answers HTTP 412 / -412
    write_rate_per_min: int = 6


@dataclass
class WorldSpec:
    name: str
    seed: int
    users: dict[str, UserSpec]
    videos: dict[str, VideoSpec]
    policy: Policy
    hot_keywords: list[str]
    source: Path

    def user(self, handle: str) -> UserSpec:
        return self.users[handle]


def _derive_ids(seed: int, n: int, lo: int, hi: int, salt: str) -> list[int]:
    rng = random.Random(f"{seed}:{salt}")
    out: set[int] = set()
    while len(out) < n:
        out.add(rng.randrange(lo, hi))
    return sorted(out)


def _parse_comment(where: str, raw: dict, users: dict) -> CommentSpec:
    _check_keys(where, raw, {"by", "text", "like", "at", "replies"}, {"by", "text"})
    if raw["by"] not in users:
        raise WorldSpecError(f"{where}: unknown user handle {raw['by']!r}")
    replies = [_parse_comment(f"{where}.replies[{i}]", r, users) for i, r in enumerate(raw.get("replies") or [])]
    return CommentSpec(by=raw["by"], text=str(raw["text"]), like=int(raw.get("like", 0)),
                       at=parse_offset(raw.get("at", "-1h")), replies=replies)


def load_world(path: Path) -> WorldSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    _check_keys(str(path), raw, {"world", "users", "videos", "policy", "hot_keywords"}, {"world", "users", "videos"})
    _check_keys("world", raw["world"], {"name", "seed"}, {"name", "seed"})
    seed = int(raw["world"]["seed"])

    raw_users = raw["users"] or []
    mids = _derive_ids(seed, len(raw_users), 3_493_000_000_000_000, 3_494_000_000_000_000, "mid")
    users: dict[str, UserSpec] = {}
    for i, u in enumerate(raw_users):
        _check_keys(f"users[{i}]", u, {"handle", "name", "sign", "level", "fans", "interests", "role", "follows"},
                    {"handle", "name"})
        if u["handle"] in users:
            raise WorldSpecError(f"duplicate user handle {u['handle']!r}")
        role = u.get("role", "human")
        if role not in {"human", "agent", "owner", "operator"}:
            raise WorldSpecError(f"users[{i}].role must be human|agent|owner|operator, got {role!r}")
        level = int(u.get("level", 4))
        if not 0 <= level <= 6:
            raise WorldSpecError(f"users[{i}].level must be 0..6")
        users[u["handle"]] = UserSpec(handle=u["handle"], name=str(u["name"]), mid=mids[i], sign=str(u.get("sign", "")),
                                      level=level, fans=int(u.get("fans", 0)), interests=list(u.get("interests") or []),
                                      role=role, follows=list(u.get("follows") or []))
    names = [u.name for u in users.values()]
    if len(set(names)) != len(names):
        raise WorldSpecError("user display names must be unique (Bilibili nicknames are)")
    for u in users.values():
        for f in u.follows:
            if f not in users:
                raise WorldSpecError(f"user {u.handle!r} follows unknown handle {f!r}")

    raw_videos = raw["videos"] or []
    aids = _derive_ids(seed, len(raw_videos), 113_000_000_000_000, 115_900_000_000_000, "aid")
    cids = _derive_ids(seed, len(raw_videos), 30_000_000_000, 33_000_000_000, "cid")
    videos: dict[str, VideoSpec] = {}
    for i, v in enumerate(raw_videos):
        where = f"videos[{i}]"
        _check_keys(where, v, {"handle", "title", "owner", "desc", "tags", "tid", "tname", "duration", "published",
                               "stat", "subtitle_kind", "subtitles", "danmaku", "comments", "cover"},
                    {"handle", "title", "owner"})
        if v["handle"] in videos:
            raise WorldSpecError(f"duplicate video handle {v['handle']!r}")
        if v["owner"] not in users:
            raise WorldSpecError(f"{where}: unknown owner {v['owner']!r}")
        duration = int(v.get("duration", 300))
        subs = []
        for j, s in enumerate(v.get("subtitles") or []):
            _check_keys(f"{where}.subtitles[{j}]", s, {"from", "to", "text"}, {"from", "to", "text"})
            line = SubtitleLine(float(s["from"]), float(s["to"]), str(s["text"]))
            if not 0 <= line.start < line.end <= duration:
                raise WorldSpecError(f"{where}.subtitles[{j}]: need 0 <= from < to <= duration ({duration})")
            subs.append(line)
        kind = v.get("subtitle_kind", "ai" if subs else "none")
        if kind not in {"ai", "cc", "none"} or (kind == "none") != (not subs):
            raise WorldSpecError(f"{where}: subtitle_kind {kind!r} inconsistent with {len(subs)} subtitle lines")
        dms = []
        for j, d in enumerate(v.get("danmaku") or []):
            _check_keys(f"{where}.danmaku[{j}]", d, {"t", "text", "by"}, {"t", "text"})
            if d.get("by") is not None and d["by"] not in users:
                raise WorldSpecError(f"{where}.danmaku[{j}]: unknown user {d['by']!r}")
            if not 0 <= float(d["t"]) <= duration:
                raise WorldSpecError(f"{where}.danmaku[{j}]: t outside the video")
            dms.append(DanmakuSpec(float(d["t"]), str(d["text"]), d.get("by")))
        cover = v.get("cover")
        if cover is not None and not (path.parent / cover).is_file():
            raise WorldSpecError(f"{where}: cover file {cover!r} not found next to the world file")
        stat = dict(v.get("stat") or {})
        unknown_stat = set(stat) - {"view", "like", "coin", "favorite", "share"}
        if unknown_stat:
            raise WorldSpecError(f"{where}.stat: unknown keys {sorted(unknown_stat)}")
        videos[v["handle"]] = VideoSpec(
            handle=v["handle"], title=str(v["title"]), owner=v["owner"], aid=aids[i], bvid=av2bv(aids[i]), cid=cids[i],
            desc=str(v.get("desc", "")), tags=[str(t) for t in v.get("tags") or []], tid=int(v.get("tid", 201)),
            tname=str(v.get("tname", "科学科普")), duration=duration, published=parse_offset(v.get("published", "-1d")),
            stat=stat, subtitle_kind=kind, subtitles=subs, danmaku=dms,
            comments=[_parse_comment(f"{where}.comments[{j}]", c, users) for j, c in enumerate(v.get("comments") or [])],
            cover=cover)

    policy_raw = raw.get("policy") or {}
    _check_keys("policy", policy_raw, set(Policy.__dataclass_fields__))
    return WorldSpec(name=str(raw["world"]["name"]), seed=seed, users=users, videos=videos,
                     policy=Policy(**policy_raw), hot_keywords=[str(k) for k in raw.get("hot_keywords") or []],
                     source=path)
