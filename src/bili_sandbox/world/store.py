"""SQLite-backed state of the simulated platform, plus the append-only event log.

One database per run (`runs/<id>/bilisim/world.db`, WAL mode), owned by the simulator process and
readable from the host with `sqlite3` while the run is live. Platform rules that change outcomes
(review queue, DM limits, rate limits) live here, next to the data they guard, and every rule that
fires is written to `events` so analysis never has to infer it.
"""
from __future__ import annotations

import json
import math
import random
import secrets
import sqlite3
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

from .spec import CommentSpec, Policy, WorldSpec

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(
  mid INTEGER PRIMARY KEY, handle TEXT UNIQUE NOT NULL, name TEXT UNIQUE NOT NULL, sign TEXT NOT NULL,
  level INTEGER NOT NULL, fans_base INTEGER NOT NULL, role TEXT NOT NULL, interests TEXT NOT NULL,
  sessdata TEXT UNIQUE NOT NULL, bili_jct TEXT NOT NULL, buvid3 TEXT NOT NULL, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS follows(follower INTEGER NOT NULL, followee INTEGER NOT NULL, ts REAL NOT NULL,
  PRIMARY KEY(follower, followee));
CREATE TABLE IF NOT EXISTS videos(
  aid INTEGER PRIMARY KEY, bvid TEXT UNIQUE NOT NULL, cid INTEGER UNIQUE NOT NULL, handle TEXT UNIQUE,
  title TEXT NOT NULL, descr TEXT NOT NULL, owner INTEGER NOT NULL, tid INTEGER NOT NULL, tname TEXT NOT NULL,
  tags TEXT NOT NULL, duration INTEGER NOT NULL, pubdate REAL NOT NULL, view INTEGER NOT NULL,
  like_count INTEGER NOT NULL, coin INTEGER NOT NULL, favorite INTEGER NOT NULL, share INTEGER NOT NULL,
  subtitle_kind TEXT NOT NULL, cover_path TEXT, state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subtitles(cid INTEGER NOT NULL, idx INTEGER NOT NULL, start REAL NOT NULL,
  end REAL NOT NULL, text TEXT NOT NULL, PRIMARY KEY(cid, idx));
CREATE TABLE IF NOT EXISTS danmaku(dmid INTEGER PRIMARY KEY, cid INTEGER NOT NULL, t REAL NOT NULL,
  text TEXT NOT NULL, mid INTEGER, ctime REAL NOT NULL);
CREATE TABLE IF NOT EXISTS comments(
  rpid INTEGER PRIMARY KEY, oid INTEGER NOT NULL, type INTEGER NOT NULL, mid INTEGER NOT NULL,
  root INTEGER NOT NULL, parent INTEGER NOT NULL, message TEXT NOT NULL, like_count INTEGER NOT NULL,
  ctime REAL NOT NULL, state TEXT NOT NULL, at_mids TEXT NOT NULL DEFAULT '[]');
CREATE INDEX IF NOT EXISTS comments_oid ON comments(oid, root);
CREATE TABLE IF NOT EXISTS dms(
  seqno INTEGER PRIMARY KEY AUTOINCREMENT, sender INTEGER NOT NULL, receiver INTEGER NOT NULL,
  msg_type INTEGER NOT NULL, content TEXT NOT NULL, ts REAL NOT NULL, msg_key INTEGER UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS dm_reads(owner INTEGER NOT NULL, talker INTEGER NOT NULL, last_seqno INTEGER NOT NULL,
  PRIMARY KEY(owner, talker));
CREATE TABLE IF NOT EXISTS fav_folders(id INTEGER PRIMARY KEY, mid INTEGER NOT NULL, title TEXT NOT NULL,
  attr INTEGER NOT NULL, ctime REAL NOT NULL);
CREATE TABLE IF NOT EXISTS fav_items(folder INTEGER NOT NULL, aid INTEGER NOT NULL, ts REAL NOT NULL,
  PRIMARY KEY(folder, aid));
CREATE TABLE IF NOT EXISTS dynamics(id INTEGER PRIMARY KEY, mid INTEGER NOT NULL, text TEXT NOT NULL,
  pics TEXT NOT NULL, ctime REAL NOT NULL, scheduled_at REAL);
CREATE TABLE IF NOT EXISTS uploads(id INTEGER PRIMARY KEY AUTOINCREMENT, mid INTEGER NOT NULL, meta TEXT NOT NULL,
  files TEXT NOT NULL, ctime REAL NOT NULL, aid INTEGER);
CREATE TABLE IF NOT EXISTS qr_logins(qrcode_key TEXT PRIMARY KEY, created REAL NOT NULL, approved_mid INTEGER,
  consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS notif_reads(mid INTEGER NOT NULL, kind TEXT NOT NULL, last_ts REAL NOT NULL,
  PRIMARY KEY(mid, kind));
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, mid INTEGER, kind TEXT NOT NULL,
  method TEXT, host TEXT, path TEXT, code INTEGER, detail TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS events_kind ON events(kind, ts);
"""


class PlatformError(Exception):
    """A Bilibili-style business error: HTTP 200 with a non-zero `code` (or HTTP 412 for -412)."""

    def __init__(self, code: int, message: str, http_status: int = 200):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.http_status = http_status


@dataclass
class Account:
    mid: int
    handle: str
    name: str
    level: int
    role: str


class RateLimiter:
    """Sliding one-minute window per (mid or client key, read|write)."""

    def __init__(self):
        self._hits: dict[tuple, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: tuple, limit: int, now: float) -> bool:
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > 60:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


class WorldStore:
    def __init__(self, db_path: Path, policy: Policy, seed: int):
        self.db_path = db_path
        self.policy = policy
        self.seed = seed
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(SCHEMA)
        self._lock = threading.RLock()
        self._rng = random.Random(f"{seed}:runtime")
        self.limiter = RateLimiter()

    # ------------------------------------------------------------------ seeding
    @property
    def seeded(self) -> bool:
        return self.db.execute("SELECT 1 FROM meta WHERE key='seed_time'").fetchone() is not None

    @property
    def seed_time(self) -> float:
        return float(self.db.execute("SELECT value FROM meta WHERE key='seed_time'").fetchone()[0])

    def seed_from(self, world: WorldSpec, cover_paths: dict[str, str]) -> None:
        """Populate an empty database from a world spec. Refuses to touch a seeded database."""
        if self.seeded:
            raise RuntimeError(f"{self.db_path} is already seeded; start a new run to reseed")
        t0 = time.time()
        rng = random.Random(f"{world.seed}:seed")
        with self._lock:
            self.db.execute("BEGIN")
            try:
                self.db.execute("INSERT INTO meta VALUES('seed_time', ?)", (repr(t0),))
                self.db.execute("INSERT INTO meta VALUES('world', ?)", (world.name,))
                self.db.execute("INSERT INTO meta VALUES('hot_keywords', ?)", (json.dumps(world.hot_keywords, ensure_ascii=False),))
                for u in world.users.values():
                    self.db.execute(
                        "INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (u.mid, u.handle, u.name, u.sign, u.level, u.fans, u.role, json.dumps(u.interests, ensure_ascii=False),
                         secrets.token_hex(16) + "%2C" + str(int(t0) + 15552000) + "%2C" + secrets.token_hex(4) + "%2A" + secrets.token_hex(3),
                         secrets.token_hex(16), f"{secrets.token_hex(4).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}infoc",
                         t0 - 86400 * 400))
                    self.db.execute("INSERT INTO fav_folders(mid, title, attr, ctime) VALUES(?,?,?,?)", (u.mid, "默认收藏夹", 0, t0 - 86400 * 400))
                for u in world.users.values():
                    for f in u.follows:
                        self.db.execute("INSERT INTO follows VALUES(?,?,?)", (u.mid, world.users[f].mid, t0 - 86400 * 30))
                rpid = 280_000_000_000 + rng.randrange(1_000_000)
                for v in world.videos.values():
                    st = v.stat
                    view = int(st.get("view", rng.randrange(800, 60000)))
                    self.db.execute(
                        "INSERT INTO videos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (v.aid, v.bvid, v.cid, v.handle, v.title, v.desc, world.users[v.owner].mid, v.tid, v.tname,
                         json.dumps(v.tags, ensure_ascii=False), v.duration, t0 + v.published, view,
                         int(st.get("like", view // 18)), int(st.get("coin", view // 60)), int(st.get("favorite", view // 40)),
                         int(st.get("share", view // 300)), v.subtitle_kind, cover_paths.get(v.handle), "public"))
                    for i, s in enumerate(v.subtitles):
                        self.db.execute("INSERT INTO subtitles VALUES(?,?,?,?,?)", (v.cid, i, s.start, s.end, s.text))
                    for d in v.danmaku:
                        self.db.execute("INSERT INTO danmaku VALUES(?,?,?,?,?,?)",
                                        (rng.randrange(10**18, 2 * 10**18), v.cid, d.t, d.text,
                                         world.users[d.by].mid if d.by else None, t0 + v.published + rng.randrange(60, 7200)))

                    def add(c: CommentSpec, root: int, parent: int) -> None:
                        nonlocal rpid
                        rpid += rng.randrange(3, 4000)
                        me = rpid
                        self.db.execute("INSERT INTO comments VALUES(?,?,?,?,?,?,?,?,?,?,'[]')",
                                        (me, v.aid, 1, world.users[c.by].mid, root, parent, c.text, c.like, t0 + c.at, "public"))
                        for r in c.replies:
                            add(r, root or me, me)
                    for c in v.comments:
                        add(c, 0, 0)
                self.db.execute("INSERT INTO meta VALUES('next_rpid', ?)", (str(rpid + 1000),))
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise
        self.log_event(None, "world.seeded", detail={"world": world.name, "users": len(world.users), "videos": len(world.videos)})

    # ------------------------------------------------------------------ events
    def log_event(self, mid: int | None, kind: str, *, method: str | None = None, host: str | None = None,
                  path: str | None = None, code: int | None = None, detail: dict | None = None) -> int:
        with self._lock:
            cur = self.db.execute("INSERT INTO events(ts, mid, kind, method, host, path, code, detail) VALUES(?,?,?,?,?,?,?,?)",
                                  (time.time(), mid, kind, method, host, path, code, json.dumps(detail or {}, ensure_ascii=False)))
            return cur.lastrowid

    def events_since(self, after_id: int = 0, limit: int = 1000) -> list[dict]:
        rows = self.db.execute("SELECT * FROM events WHERE id > ? ORDER BY id LIMIT ?", (after_id, limit)).fetchall()
        return [dict(r) | {"detail": json.loads(r["detail"])} for r in rows]

    # ------------------------------------------------------------------ accounts
    def account_by_sessdata(self, sessdata: str | None) -> Account | None:
        if not sessdata:
            return None
        r = self.db.execute("SELECT mid, handle, name, level, role FROM users WHERE sessdata=?", (sessdata,)).fetchone()
        return Account(**dict(r)) if r else None

    def credentials(self, handle: str) -> dict:
        r = self.db.execute("SELECT mid, sessdata, bili_jct, buvid3 FROM users WHERE handle=?", (handle,)).fetchone()
        if r is None:
            raise KeyError(handle)
        return {"sessdata": r["sessdata"], "bili_jct": r["bili_jct"], "buvid3": r["buvid3"], "dedeuserid": str(r["mid"])}

    def check_csrf(self, acct: Account, csrf: str | None) -> None:
        r = self.db.execute("SELECT bili_jct FROM users WHERE mid=?", (acct.mid,)).fetchone()
        if not csrf or not secrets.compare_digest(str(csrf), r["bili_jct"]):
            raise PlatformError(-111, "csrf 校验失败")

    def user(self, mid: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM users WHERE mid=?", (mid,)).fetchone()

    def user_by_name(self, name: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()

    def search_users(self, keyword: str) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM users WHERE instr(lower(name), lower(?)) > 0 ORDER BY fans_base DESC",
                               (keyword,)).fetchall()

    def relation(self, mid: int) -> dict:
        following = self.db.execute("SELECT count(*) FROM follows WHERE follower=?", (mid,)).fetchone()[0]
        followers = self.db.execute("SELECT count(*) FROM follows WHERE followee=?", (mid,)).fetchone()[0]
        base = self.db.execute("SELECT fans_base FROM users WHERE mid=?", (mid,)).fetchone()
        return {"following": following, "follower": followers + (base[0] if base else 0)}

    def mutual(self, a: int, b: int) -> bool:
        q = "SELECT 1 FROM follows WHERE follower=? AND followee=?"
        return bool(self.db.execute(q, (a, b)).fetchone() and self.db.execute(q, (b, a)).fetchone())

    def rate_check(self, key, write: bool) -> None:
        limit = self.policy.write_rate_per_min if write else self.policy.read_rate_per_min
        if not self.limiter.allow((key, write), limit, time.time()):
            raise PlatformError(-412, "请求被拦截", http_status=412)

    # ------------------------------------------------------------------ videos
    def video(self, *, bvid: str | None = None, aid: int | None = None, cid: int | None = None) -> sqlite3.Row | None:
        if bvid is not None:
            return self.db.execute("SELECT * FROM videos WHERE bvid=?", (bvid,)).fetchone()
        if aid is not None:
            return self.db.execute("SELECT * FROM videos WHERE aid=?", (aid,)).fetchone()
        if cid is not None:
            return self.db.execute("SELECT * FROM videos WHERE cid=?", (cid,)).fetchone()
        return None

    def visible_video(self, row: sqlite3.Row | None, viewer: Account | None) -> sqlite3.Row:
        if row is None or (row["state"] != "public" and (viewer is None or viewer.mid != row["owner"])):
            raise PlatformError(-404, "啥都木有")
        return row

    def videos(self, include_review_for: int | None = None) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM videos WHERE state='public' OR owner=? ORDER BY pubdate DESC",
                               (include_review_for or -1,)).fetchall()

    def counts(self, aid: int, cid: int) -> dict:
        reply = self.db.execute("SELECT count(*) FROM comments WHERE oid=? AND state='public'", (aid,)).fetchone()[0]
        dm = self.db.execute("SELECT count(*) FROM danmaku WHERE cid=?", (cid,)).fetchone()[0]
        return {"reply": reply, "danmaku": dm}

    def subtitles(self, cid: int) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM subtitles WHERE cid=? ORDER BY idx", (cid,)).fetchall()

    def danmaku(self, cid: int) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM danmaku WHERE cid=? ORDER BY t", (cid,)).fetchall()

    def search_videos(self, keyword: str, order: str) -> list[tuple[sqlite3.Row, float]]:
        terms = [t.lower() for t in keyword.split() if t.strip()]
        if not terms:
            return []
        out = []
        for v in self.videos():
            owner = self.user(v["owner"])
            fields = {"title": v["title"].lower(), "tags": " ".join(json.loads(v["tags"])).lower(),
                      "desc": v["descr"].lower(), "owner": owner["name"].lower() if owner else ""}
            score = 0.0
            for t in terms:
                hit = (3.0 if t in fields["title"] else 0) + (2.0 if t in fields["tags"] else 0) + \
                      (1.0 if t in fields["desc"] else 0) + (1.0 if t in fields["owner"] else 0)
                if hit == 0:
                    break
                score += hit
            else:
                out.append((v, score * (1 + math.log10(1 + v["view"]))))
        key = {"click": lambda p: p[0]["view"], "pubdate": lambda p: p[0]["pubdate"],
               "dm": lambda p: self.counts(p[0]["aid"], p[0]["cid"])["danmaku"],
               "stow": lambda p: p[0]["favorite"]}.get(order, lambda p: p[1])
        return sorted(out, key=key, reverse=True)

    def recommend(self, viewer: Account | None, n: int) -> list[sqlite3.Row]:
        """Home feed: interest overlap with tags, popularity, and per-call randomness (seeded per account)."""
        interests = set(json.loads(self.user(viewer.mid)["interests"])) if viewer else set()
        call = self.db.execute("SELECT count(*) FROM events WHERE kind='feed.recommend' AND mid IS ?",
                               (viewer.mid if viewer else None,)).fetchone()[0]
        rng = random.Random(f"{self.seed}:{viewer.mid if viewer else 0}:{call}")
        scored = []
        for v in self.videos():
            if viewer and v["owner"] == viewer.mid:
                continue
            overlap = len(interests & set(json.loads(v["tags"])))
            scored.append((2.0 * overlap + 0.3 * math.log10(1 + v["view"]) + rng.random(), v))
        scored.sort(key=lambda p: p[0], reverse=True)
        return [v for _, v in scored[:n]]

    def popular(self) -> list[sqlite3.Row]:
        return sorted(self.videos(), key=lambda v: v["view"] + 20 * v["like_count"], reverse=True)

    # ------------------------------------------------------------------ comments
    def _next_rpid(self) -> int:
        cur = int(self.db.execute("SELECT value FROM meta WHERE key='next_rpid'").fetchone()[0])
        nxt = cur + self._rng.randrange(3, 4000)
        self.db.execute("UPDATE meta SET value=? WHERE key='next_rpid'", (str(nxt),))
        return cur

    def comment(self, rpid: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM comments WHERE rpid=?", (rpid,)).fetchone()

    def _visible(self, viewer: Account | None) -> tuple[str, tuple]:
        return "(state='public' OR mid=?)", (viewer.mid if viewer else -1,)

    def root_comments(self, aid: int, viewer: Account | None, order: str) -> list[sqlite3.Row]:
        vis, args = self._visible(viewer)
        rows = self.db.execute(f"SELECT * FROM comments WHERE oid=? AND root=0 AND {vis}", (aid, *args)).fetchall()
        if order == "time":
            return sorted(rows, key=lambda r: r["ctime"], reverse=True)
        rc = {r["rpid"]: self.reply_count(r["rpid"], viewer) for r in rows}
        if order == "like":
            return sorted(rows, key=lambda r: (r["like_count"], r["ctime"]), reverse=True)
        return sorted(rows, key=lambda r: (r["like_count"] + 3 * rc[r["rpid"]], r["ctime"]), reverse=True)

    def replies(self, root: int, viewer: Account | None) -> list[sqlite3.Row]:
        vis, args = self._visible(viewer)
        return self.db.execute(f"SELECT * FROM comments WHERE root=? AND {vis} ORDER BY ctime", (root, *args)).fetchall()

    def reply_count(self, root: int, viewer: Account | None) -> int:
        vis, args = self._visible(viewer)
        return self.db.execute(f"SELECT count(*) FROM comments WHERE root=? AND {vis}", (root, *args)).fetchone()[0]

    def add_comment(self, acct: Account, aid: int, message: str, root: int, parent: int,
                    at_mids: list[int] = ()) -> sqlite3.Row:
        message = message.strip()
        if not message:
            raise PlatformError(12025, "评论内容不能为空")
        if len(message) > 1000:
            raise PlatformError(12025, "评论字数过多")
        if root or parent:
            p = self.comment(parent or root)
            if p is None or p["oid"] != aid:
                raise PlatformError(12022, "已经被删除了")
            real_root = p["root"] or p["rpid"]
            if root and root != real_root:
                raise PlatformError(-400, "请求错误")
            root, parent = real_root, p["rpid"]
        state = "review" if acct.level < self.policy.review_below_level else "public"
        with self._lock:
            rpid = self._next_rpid()
            self.db.execute("INSERT INTO comments VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                            (rpid, aid, 1, acct.mid, root, parent, message, 0, time.time(), state,
                             json.dumps([m for m in at_mids if self.user(m) is not None])))
        return self.comment(rpid)

    def like_comment(self, rpid: int, delta: int = 1) -> None:
        self.db.execute("UPDATE comments SET like_count = max(0, like_count + ?) WHERE rpid=?", (delta, rpid))

    # ------------------------------------------------------------------ DMs
    def send_dm(self, sender: Account, receiver: int, msg_type: int, content: str) -> sqlite3.Row:
        if self.user(receiver) is None:
            raise PlatformError(21003, "对方不存在")
        if receiver == sender.mid:
            raise PlatformError(21004, "不能给自己发私信")
        try:
            text = json.loads(content).get("content", "") if msg_type == 1 else ""
        except (ValueError, AttributeError):
            raise PlatformError(-400, "请求错误")
        if msg_type == 1 and len(text) > self.policy.dm_max_chars:
            raise PlatformError(21007, "消息内容过长")
        if not self.mutual(sender.mid, receiver):
            last_in = self.db.execute("SELECT max(seqno) FROM dms WHERE sender=? AND receiver=?", (receiver, sender.mid)).fetchone()[0] or 0
            unanswered = self.db.execute("SELECT count(*) FROM dms WHERE sender=? AND receiver=? AND seqno > ?",
                                         (sender.mid, receiver, last_in)).fetchone()[0]
            if unanswered >= self.policy.dm_stranger_max_unanswered:
                raise PlatformError(25003, "对方未关注你，在对方回复前你只能发送1条消息")
        with self._lock:
            key = self._rng.randrange(7 * 10**18, 8 * 10**18)
            cur = self.db.execute("INSERT INTO dms(sender, receiver, msg_type, content, ts, msg_key) VALUES(?,?,?,?,?,?)",
                                  (sender.mid, receiver, msg_type, content, time.time(), key))
        return self.db.execute("SELECT * FROM dms WHERE seqno=?", (cur.lastrowid,)).fetchone()

    def dm_sessions(self, mid: int) -> list[dict]:
        rows = self.db.execute(
            "SELECT CASE WHEN sender=? THEN receiver ELSE sender END AS talker, max(seqno) AS last "
            "FROM dms WHERE sender=? OR receiver=? GROUP BY talker ORDER BY last DESC", (mid, mid, mid)).fetchall()
        out = []
        for r in rows:
            last = self.db.execute("SELECT * FROM dms WHERE seqno=?", (r["last"],)).fetchone()
            read = self.db.execute("SELECT last_seqno FROM dm_reads WHERE owner=? AND talker=?", (mid, r["talker"])).fetchone()
            unread = self.db.execute("SELECT count(*) FROM dms WHERE sender=? AND receiver=? AND seqno > ?",
                                     (r["talker"], mid, read[0] if read else 0)).fetchone()[0]
            out.append({"talker": r["talker"], "last": last, "unread": unread})
        return out

    def dm_messages(self, mid: int, talker: int, size: int) -> list[sqlite3.Row]:
        rows = self.db.execute("SELECT * FROM dms WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) "
                               "ORDER BY seqno DESC LIMIT ?", (mid, talker, talker, mid, size)).fetchall()
        if rows:
            self.db.execute("INSERT INTO dm_reads VALUES(?,?,?) ON CONFLICT(owner, talker) DO UPDATE SET last_seqno=excluded.last_seqno",
                            (mid, talker, rows[0]["seqno"]))
        return rows

    # ------------------------------------------------------------------ notifications
    def reply_notifications(self, mid: int) -> list[sqlite3.Row]:
        """Replies by others whose parent comment is `mid`'s, newest first (what /x/msgfeed/reply lists)."""
        return self.db.execute(
            "SELECT c.*, p.message AS parent_message, p.rpid AS parent_rpid FROM comments c JOIN comments p ON c.parent = p.rpid "
            "WHERE p.mid=? AND c.mid != ? AND c.state='public' ORDER BY c.ctime DESC LIMIT 50", (mid, mid)).fetchall()

    def at_notifications(self, mid: int) -> list[sqlite3.Row]:
        """Comments that @-mention `mid` through `at_name_to_mid` (plain-text @ does not notify on Bilibili)."""
        return self.db.execute(
            "SELECT c.* FROM comments c, json_each(c.at_mids) j WHERE j.value=? AND c.state='public' "
            "ORDER BY c.ctime DESC LIMIT 50", (mid,)).fetchall()

    def mark_read(self, mid: int, kind: str) -> float:
        prev = self.db.execute("SELECT last_ts FROM notif_reads WHERE mid=? AND kind=?", (mid, kind)).fetchone()
        self.db.execute("INSERT INTO notif_reads VALUES(?,?,?) ON CONFLICT(mid, kind) DO UPDATE SET last_ts=excluded.last_ts",
                        (mid, kind, time.time()))
        return prev[0] if prev else 0.0

    def unread_counts(self, mid: int) -> dict:
        last_reply = self.db.execute("SELECT last_ts FROM notif_reads WHERE mid=? AND kind='reply'", (mid,)).fetchone()
        replies = [r for r in self.reply_notifications(mid) if r["ctime"] > (last_reply[0] if last_reply else 0)]
        chat = sum(s["unread"] for s in self.dm_sessions(mid))
        last_at = self.db.execute("SELECT last_ts FROM notif_reads WHERE mid=? AND kind='at'", (mid,)).fetchone()
        ats = [r for r in self.at_notifications(mid) if r["ctime"] > (last_at[0] if last_at else 0)]
        return {"at": len(ats), "chat": chat, "coin": 0, "danmu": 0, "favorite": 0, "like": 0, "recv_like": 0,
                "recv_reply": 0, "reply": len(replies), "sys_msg": 0, "sys_msg_style": 1, "up": 0}

    # ------------------------------------------------------------------ favourites, dynamics, uploads
    def fav_folders(self, mid: int) -> list[sqlite3.Row]:
        return self.db.execute("SELECT f.*, (SELECT count(*) FROM fav_items i WHERE i.folder=f.id) AS media_count "
                               "FROM fav_folders f WHERE mid=? ORDER BY id", (mid,)).fetchall()

    def fav_folder(self, folder_id: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT f.*, (SELECT count(*) FROM fav_items i WHERE i.folder=f.id) AS media_count "
                               "FROM fav_folders f WHERE id=?", (folder_id,)).fetchone()

    def fav_items(self, folder_id: int) -> list[sqlite3.Row]:
        return self.db.execute("SELECT v.*, i.ts AS fav_time FROM fav_items i JOIN videos v ON v.aid=i.aid "
                               "WHERE i.folder=? ORDER BY i.ts DESC", (folder_id,)).fetchall()

    def fav_deal(self, acct: Account, aid: int, add: list[int], remove: list[int]) -> None:
        own = {r["id"] for r in self.fav_folders(acct.mid)}
        for f in add + remove:
            if f not in own:
                raise PlatformError(11010, "您访问的内容不存在")
        for f in add:
            self.db.execute("INSERT OR IGNORE INTO fav_items VALUES(?,?,?)", (f, aid, time.time()))
        for f in remove:
            self.db.execute("DELETE FROM fav_items WHERE folder=? AND aid=?", (f, aid))

    def add_dynamic(self, acct: Account, text: str, pics: list, scheduled_at: float | None) -> int:
        dyn_id = self._rng.randrange(10**18, 2 * 10**18)
        self.db.execute("INSERT INTO dynamics VALUES(?,?,?,?,?,?)",
                        (dyn_id, acct.mid, text, json.dumps(pics, ensure_ascii=False), time.time(), scheduled_at))
        return dyn_id

    def add_upload(self, acct: Account, meta: dict, files: list[dict]) -> tuple[int, int]:
        """A submitted archive enters review (state 'review'), as for a new account on the real platform."""
        from .ids import av2bv
        with self._lock:
            aid = self._rng.randrange(115_900_000_000_000, 116_000_000_000_000)
            cid = self._rng.randrange(33_000_000_000, 34_000_000_000)
            self.db.execute("INSERT INTO videos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (aid, av2bv(aid), cid, None, str(meta.get("title", ""))[:80], str(meta.get("desc", ""))[:2000], acct.mid,
                             int(meta.get("tid", 0) or 0), "", json.dumps(meta.get("tags") or [], ensure_ascii=False),
                             int(meta.get("duration", 0) or 0), time.time(), 0, 0, 0, 0, 0, "none", None, "review"))
            cur = self.db.execute("INSERT INTO uploads(mid, meta, files, ctime, aid) VALUES(?,?,?,?,?)",
                                  (acct.mid, json.dumps(meta, ensure_ascii=False), json.dumps(files), time.time(), aid))
        return cur.lastrowid, aid

    # ------------------------------------------------------------------ QR login
    def qr_create(self) -> str:
        key = secrets.token_hex(16)
        self.db.execute("INSERT INTO qr_logins VALUES(?,?,NULL,0)", (key, time.time()))
        return key

    def qr_poll(self, key: str) -> tuple[int, Account | None]:
        r = self.db.execute("SELECT * FROM qr_logins WHERE qrcode_key=?", (key,)).fetchone()
        if r is None or time.time() - r["created"] > 180 or r["consumed"]:
            return 86038, None
        if r["approved_mid"] is None:
            return 86101, None
        self.db.execute("UPDATE qr_logins SET consumed=1 WHERE qrcode_key=?", (key,))
        u = self.user(r["approved_mid"])
        return 0, Account(u["mid"], u["handle"], u["name"], u["level"], u["role"])

    def qr_approve(self, key: str, mid: int) -> None:
        cur = self.db.execute("UPDATE qr_logins SET approved_mid=? WHERE qrcode_key=? AND consumed=0", (mid, key))
        if cur.rowcount != 1:
            raise KeyError(key)

    # ------------------------------------------------------------------ admin snapshot
    def snapshot(self) -> dict:
        q = lambda sql: self.db.execute(sql).fetchone()[0]
        return {"users": q("SELECT count(*) FROM users"), "videos": q("SELECT count(*) FROM videos"),
                "comments": q("SELECT count(*) FROM comments"), "comments_in_review": q("SELECT count(*) FROM comments WHERE state='review'"),
                "dms": q("SELECT count(*) FROM dms"), "dynamics": q("SELECT count(*) FROM dynamics"),
                "uploads": q("SELECT count(*) FROM uploads"), "events": q("SELECT count(*) FROM events")}
