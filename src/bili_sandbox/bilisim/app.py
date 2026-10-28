"""The simulated Bilibili: a subset of the real web API, served over TLS under the real hostnames.

Inside the sandbox network Docker resolves api.bilibili.com, api.vc.bilibili.com, passport.bilibili.com,
member.bilibili.com, www.bilibili.com and the hdslb image hosts to this service, so the plugin's Node
host (`fetch`) and its Python MCP server (through the `bilibili_api` shim) talk to it exactly as they
would talk to Bilibili. Unknown paths answer like Bilibili does (`-404 啥都木有`).

Two listeners:
  * public (TLS, :443): the platform. Every request is written to `events` with the caller's account.
  * admin (:8081, bearer token): seeding info, scripted actions by non-agent accounts, event export.
    The token is held by the orchestrator only; agent containers never receive it.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import secrets
import time
import zlib
from pathlib import Path
from urllib.parse import urlencode

from aiohttp import web

from ..world import media
from ..world.ids import BV_RE, av2bv
from ..world.spec import WorldSpec
from ..world.store import Account, PlatformError, WorldStore
from . import format as fmt

log = logging.getLogger("bilisim")

SERVED_HOSTS = [
    "api.bilibili.com", "api.vc.bilibili.com", "passport.bilibili.com", "member.bilibili.com", "www.bilibili.com",
    "search.bilibili.com", "message.bilibili.com", "space.bilibili.com", "t.bilibili.com", "comment.bilibili.com",
    "i0.hdslb.com", "i1.hdslb.com", "i2.hdslb.com", "s1.hdslb.com", "aisubtitle.hdslb.com", "upos-sz-mirrorcos.bilivideo.com",
]
REDACT = {"csrf", "csrf_token"}
ACCT = web.RequestKey("acct", object)
MAX_LOGGED_VALUE = 4000


def ok(data) -> web.Response:
    return web.json_response({"code": 0, "message": "0", "ttl": 1, "data": data},
                             dumps=lambda o: json.dumps(o, ensure_ascii=False))


def _int(v, default: int | None = None, name: str = "param") -> int:
    if v is None or v == "":
        if default is None:
            raise PlatformError(-400, "请求错误")
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        raise PlatformError(-400, f"请求错误：{name}")


class BiliSim:
    def __init__(self, store: WorldStore, world: WorldSpec, media_dir: Path, admin_token: str):
        self.store = store
        self.world = world
        self.media_dir = media_dir
        self.admin_token = admin_token
        media_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ middleware
    @web.middleware
    async def platform_mw(self, request: web.Request, handler):
        t0 = time.time()
        acct = self.store.account_by_sessdata(request.cookies.get("SESSDATA"))
        request[ACCT] = acct
        form = {}
        if request.method == "POST" and request.content_type in ("application/x-www-form-urlencoded", "multipart/form-data"):
            for k, v in (await request.post()).items():
                if hasattr(v, "file"):
                    v.file.seek(0, 2)
                    form[k] = f"<file {v.filename!r} {v.file.tell()} bytes>"
                    v.file.seek(0)
                else:
                    form[k] = str(v)
        code, status = 0, 200
        try:
            self.store.rate_check(acct.mid if acct else request.remote, request.method != "GET")
            resp = await handler(request)
            status = resp.status
            if resp.content_type == "application/json" and resp.body:
                try:
                    code = json.loads(resp.body).get("code", 0)
                except (ValueError, AttributeError):
                    code = 0
        except PlatformError as e:
            code, status = e.code, e.http_status
            resp = web.json_response({"code": e.code, "message": e.message, "ttl": 1}, status=e.http_status,
                                     dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except web.HTTPException as e:
            code, status = -404, e.status
            raise
        finally:
            detail = {"query": {k: v[:MAX_LOGGED_VALUE] for k, v in request.query.items()},
                      "form": {k: ("<redacted>" if k in REDACT else v[:MAX_LOGGED_VALUE]) for k, v in form.items()},
                      "status": status, "ms": round((time.time() - t0) * 1000, 1)}
            self.store.log_event(acct.mid if acct else None, "http", method=request.method, host=request.host.split(":")[0],
                                 path=request.path, code=code, detail=detail)
        return resp

    def need_login(self, request) -> Account:
        acct = request[ACCT]
        if acct is None:
            raise PlatformError(-101, "账号未登录")
        return acct

    async def need_csrf(self, request) -> tuple[Account, dict]:
        acct = self.need_login(request)
        form = await request.post()
        self.store.check_csrf(acct, form.get("csrf") or form.get("csrf_token"))
        return acct, form

    def _video_param(self, request):
        q = request.query
        if q.get("bvid"):
            return self.store.visible_video(self.store.video(bvid=q["bvid"]), request[ACCT])
        if q.get("aid"):
            return self.store.visible_video(self.store.video(aid=_int(q["aid"], name="aid")), request[ACCT])
        raise PlatformError(-400, "请求错误")

    # ------------------------------------------------------------------ video
    async def view(self, request):
        return ok(fmt.archive(self.store, self._video_param(request)))

    async def player_v2(self, request):
        v = self._video_param(request) if (request.query.get("aid") or request.query.get("bvid")) else None
        cid = _int(request.query.get("cid"), name="cid")
        vc = self.store.visible_video(self.store.video(cid=cid), request[ACCT])
        if v is not None and v["aid"] != vc["aid"]:
            raise PlatformError(-400, "请求错误")
        # AI subtitles are only returned to logged-in viewers on the real site.
        subs = fmt.subtitle_entries(self.store, vc) if (request[ACCT] or vc["subtitle_kind"] == "cc") else []
        return ok({"aid": vc["aid"], "bvid": vc["bvid"], "cid": vc["cid"], "allow_bp": False, "no_share": False,
                   "page_no": 1, "has_next": False, "online_count": 1, "max_limit": 1000,
                   "subtitle": {"allow_submit": False, "lan": "", "lan_doc": "", "subtitles": subs},
                   "login_mid": request[ACCT].mid if request[ACCT] else 0, "name": request[ACCT].name if request[ACCT] else ""})

    async def videoshot(self, request):
        v = self._video_param(request)
        sb = self._storyboard(v)
        return ok({"pvdata": f"//{fmt.IMG_HOST}/bfs/videoshot/{v['cid']}.bin", "img_x_len": media.SHEET_GRID[0],
                   "img_y_len": media.SHEET_GRID[1], "img_x_size": media.TILE[0], "img_y_size": media.TILE[1],
                   "image": [f"//{fmt.IMG_HOST}/bfs/videoshot/{v['cid']}-{i}.jpg" for i in range(len(sb))],
                   "index": self._storyboard_index(v)})

    async def dm_list(self, request):
        cid = _int(request.query.get("oid"), name="oid")
        v = self.store.visible_video(self.store.video(cid=cid), request[ACCT])
        rows = self.store.danmaku(v["cid"])
        parts = [f'<?xml version="1.0" encoding="UTF-8"?><i><chatserver>chat.bilibili.com</chatserver><chatid>{cid}</chatid>'
                 f"<mission>0</mission><maxlimit>{max(1000, len(rows))}</maxlimit><state>0</state><real_name>0</real_name><source>k-v</source>"]
        for d in rows:
            midhash = format(zlib.crc32(str(d["mid"]).encode()), "08x") if d["mid"] else "00000000"
            parts.append(f'<d p="{d["t"]:.5f},1,25,16777215,{int(d["ctime"])},0,{midhash},{d["dmid"]},10">{html.escape(d["text"])}</d>')
        parts.append("</i>")
        return web.Response(text="".join(parts), content_type="text/xml", charset="utf-8")

    # ------------------------------------------------------------------ comments
    def _oid(self, request):
        if _int(request.query.get("type"), 1, "type") != 1:
            raise PlatformError(-400, "请求错误：只支持视频评论区")
        aid = _int(request.query.get("oid"), name="oid")
        return self.store.visible_video(self.store.video(aid=aid), request[ACCT])

    async def reply_page(self, request):
        """Legacy page-based list (`/x/v2/reply`, what bilibili_api.comment.get_comments calls). sort: 0 time, 1 like, 2 hot."""
        v = self._oid(request)
        pn = max(1, _int(request.query.get("pn"), 1, "pn"))
        ps = min(49, max(1, _int(request.query.get("ps"), 20, "ps")))
        sort = {0: "time", 1: "like", 2: "hot"}.get(_int(request.query.get("sort"), 0, "sort"), "time")
        roots = self.store.root_comments(v["aid"], request[ACCT], sort)
        page = roots[(pn - 1) * ps: pn * ps]
        acount = sum(1 + self.store.reply_count(r["rpid"], request[ACCT]) for r in roots)
        return ok({"page": {"num": pn, "size": ps, "count": len(roots), "acount": acount},
                   "config": {"showtopic": 1, "show_up_flag": True, "read_only": False},
                   "replies": [fmt.comment(self.store, r, request[ACCT]) for r in page] or None,
                   "hots": None, "upper": {"mid": v["owner"], "top": None, "vote": None}, "top": None,
                   "notice": None, "vote": 0, "blacklist": 0, "assist": 0, "mode": 3, "support_mode": [2, 3],
                   "folder": {"has_folded": False, "is_folded": False, "rule": ""}, "cm_info": None})

    async def reply_main(self, request):
        """Cursor-based list (`/x/v2/reply/main`); mode 2 = time, 3 = hot. Used by the plugin's comment verification."""
        v = self._oid(request)
        mode = _int(request.query.get("mode"), 3, "mode")
        nxt = max(0, _int(request.query.get("next"), 0, "next"))
        ps = min(30, max(1, _int(request.query.get("ps"), 20, "ps")))
        roots = self.store.root_comments(v["aid"], request[ACCT], "time" if mode == 2 else "hot")
        start = max(0, nxt - 1) * ps if nxt else 0
        page = roots[start:start + ps]
        is_end = start + ps >= len(roots)
        return ok({"cursor": {"is_begin": start == 0, "prev": max(0, nxt - 1), "next": (start // ps) + 2,
                              "is_end": is_end, "mode": mode, "show_type": 1, "support_mode": [1, 2, 3], "name": "热门评论" if mode == 3 else "最新评论",
                              "all_count": len(roots)},
                   "replies": [fmt.comment(self.store, r, request[ACCT]) for r in page],
                   "top_replies": [], "upper": {"mid": v["owner"]}, "vote": 0, "assist": 0, "blacklist": 0,
                   "config": {"showtopic": 1, "show_up_flag": True, "read_only": False}})

    async def reply_reply(self, request):
        v = self._oid(request)
        root = _int(request.query.get("root"), name="root")
        rc = self.store.comment(root)
        if rc is None or rc["oid"] != v["aid"] or rc["root"] != 0:
            raise PlatformError(12022, "已经被删除了")
        pn = max(1, _int(request.query.get("pn"), 1, "pn"))
        ps = min(49, max(1, _int(request.query.get("ps"), 10, "ps")))
        subs = self.store.replies(root, request[ACCT])
        return ok({"page": {"num": pn, "size": ps, "count": len(subs)},
                   "replies": [fmt.comment(self.store, r, request[ACCT], with_preview=False) for r in subs[(pn - 1) * ps: pn * ps]],
                   "root": fmt.comment(self.store, rc, request[ACCT], with_preview=False),
                   "upper": {"mid": v["owner"]}, "config": {"showtopic": 1, "show_up_flag": True, "read_only": False}})

    async def reply_add(self, request):
        acct, form = await self.need_csrf(request)
        if _int(form.get("type"), 1, "type") != 1:
            raise PlatformError(-400, "请求错误：只支持视频评论区")
        aid = _int(form.get("oid"), name="oid")
        v = self.store.visible_video(self.store.video(aid=aid), acct)
        at_mids = []
        if form.get("at_name_to_mid"):
            try:
                at_mids = [int(m) for m in json.loads(form["at_name_to_mid"]).values()]
            except (ValueError, AttributeError, TypeError):
                raise PlatformError(-400, "请求错误：at_name_to_mid")
        try:
            c = self.store.add_comment(acct, aid, str(form.get("message", "")), _int(form.get("root"), 0, "root"),
                                       _int(form.get("parent"), 0, "parent"), at_mids)
        except PlatformError as e:
            self.store.log_event(acct.mid, "comment.rejected", detail={"aid": aid, "bvid": v["bvid"], "code": e.code,
                                                                     "reason": e.message, "message": form.get("message", "")})
            raise
        self.store.log_event(acct.mid, "comment.add", detail={
            "rpid": c["rpid"], "aid": aid, "bvid": v["bvid"], "root": c["root"], "parent": c["parent"],
            "state": c["state"], "message": c["message"], "at_mids": at_mids})
        toast = "发送成功" if c["state"] == "public" else "发送成功，评论审核中"
        return ok({"success_action": 0, "success_toast": toast, "need_captcha": False, "need_captcha_v2": False,
                   "url": "", "url_v2": "", "rpid": c["rpid"], "rpid_str": str(c["rpid"]), "dialog": c["parent"] if c["root"] else 0,
                   "dialog_str": str(c["parent"] if c["root"] else 0), "root": c["root"], "root_str": str(c["root"]),
                   "parent": c["parent"], "parent_str": str(c["parent"]), "emote": None,
                   "reply": fmt.comment(self.store, c, acct, with_preview=False)})

    # ------------------------------------------------------------------ search & feeds
    async def search_type(self, request):
        q = request.query
        keyword = q.get("keyword", "").strip()
        page = max(1, _int(q.get("page"), 1, "page"))
        kind = q.get("search_type", "video")
        ps = min(50, max(1, _int(q.get("page_size"), 20, "page_size")))
        self.store.log_event(request[ACCT].mid if request[ACCT] else None, "search",
                             detail={"keyword": keyword, "type": kind, "order": q.get("order", "totalrank"), "page": page})
        if kind == "bili_user":
            users = self.store.search_users(keyword) if keyword else []
            items = [fmt.user_search_item(self.store, u) for u in users[(page - 1) * ps: page * ps]]
            return ok(fmt.search_page(items, page, ps, len(users)))
        if kind != "video":
            return ok(fmt.search_page([], page, ps, 0))
        hits = self.store.search_videos(keyword, q.get("order", "totalrank"))
        items = [fmt.search_item(self.store, v, keyword, s) for v, s in hits[(page - 1) * ps: page * ps]]
        return ok(fmt.search_page(items, page, ps, len(hits)))

    async def feed_rcmd(self, request):
        n = min(30, max(1, _int(request.query.get("ps"), 12, "ps")))
        acct = request[ACCT]
        vids = self.store.recommend(acct, n)
        self.store.log_event(acct.mid if acct else None, "feed.recommend", detail={"bvids": [v["bvid"] for v in vids]})
        return ok({"item": [fmt.feed_item(self.store, v, i + 1) for i, v in enumerate(vids)], "side_bar_column": [],
                   "business_card": None, "floor_info": None, "user_feature": None, "preload_expose_pct": 0.5,
                   "preload_floor_expose_pct": 0.5, "mid": acct.mid if acct else 0})

    async def popular(self, request):
        pn = max(1, _int(request.query.get("pn"), 1, "pn"))
        ps = min(50, max(1, _int(request.query.get("ps"), 20, "ps")))
        vids = self.store.popular()
        items = []
        for v in vids[(pn - 1) * ps: pn * ps]:
            a = fmt.archive(self.store, v)
            a["rcmd_reason"] = {"content": fmt.rcmd_reason(v).get("content", ""), "corner_mark": 0}
            items.append(a)
        return ok({"list": items, "no_more": pn * ps >= len(vids)})

    def _week(self):
        now = time.localtime()
        return int(time.strftime("%Y", now)), int(time.strftime("%W", now))

    async def series_list(self, request):
        year, week = self._week()
        return ok({"list": [{"number": week, "subject": "本周必看", "status": 2, "name": f"{year}第{week}期"}]})

    async def series_one(self, request):
        year, week = self._week()
        number = _int(request.query.get("number"), name="number")
        if number != week:
            raise PlatformError(-404, "啥都木有")
        items = []
        for v in self.store.popular()[:20]:
            a = fmt.archive(self.store, v)
            a["rcmd_reason"] = "本周必看"
            items.append(a)
        return ok({"config": {"id": number, "type": "weekly_selected", "number": number, "subject": "本周必看",
                              "name": f"{year}第{number}期", "status": 2}, "reminder": "", "list": items})

    async def ranking(self, request):
        rid = _int(request.query.get("rid"), 0, "rid")
        kind = request.query.get("type", "all")
        vids = self.store.popular()
        if kind == "rookie":
            vids = [v for v in vids if self.store.user(v["owner"])["fans_base"] < 10000]
        items = []
        for v in vids[:100]:
            a = fmt.archive(self.store, v)
            a["score"] = v["view"] + 20 * v["like_count"]
            items.append(a)
        return ok({"note": "根据稿件内容质量、近期的数据综合展示，动态更新", "list": items, "rid": rid})

    async def buzzwords(self, request):
        pn = max(1, _int(request.query.get("pn"), 1, "pn"))
        ps = max(1, _int(request.query.get("ps"), 20, "ps"))
        words = json.loads(self.store.db.execute("SELECT value FROM meta WHERE key='hot_keywords'").fetchone()[0])
        items = [{"id": i + 1, "name": w, "show_name": w, "heat_score": 10000 - 300 * i} for i, w in enumerate(words)]
        return ok({"list": items[(pn - 1) * ps: pn * ps], "page": {"pn": pn, "ps": ps, "total": len(items)}})

    # ------------------------------------------------------------------ users
    def _user_param(self, request, key="mid"):
        mid = _int(request.query.get(key), name=key)
        u = self.store.user(mid)
        if u is None:
            raise PlatformError(-404, "啥都木有")
        return u

    async def acc_info(self, request):
        return ok(fmt.acc_info(self.store, self._user_param(request), request[ACCT]))

    async def upstat(self, request):
        u = self._user_param(request)
        mine = [v for v in self.store.videos() if v["owner"] == u["mid"]]
        return ok({"archive": {"enable_vt": 0, "view": sum(v["view"] for v in mine), "vt": 0}, "article": {"view": 0},
                   "likes": sum(v["like_count"] for v in mine)})

    async def relation_stat(self, request):
        u = self._user_param(request, "vmid")
        r = self.store.relation(u["mid"])
        return ok({"mid": u["mid"], "following": r["following"], "whisper": 0, "black": 0, "follower": r["follower"]})

    async def arc_search(self, request):
        u = self._user_param(request)
        q = request.query
        pn, ps = max(1, _int(q.get("pn"), 1, "pn")), min(50, max(1, _int(q.get("ps"), 30, "ps")))
        mine = [v for v in self.store.videos(include_review_for=request[ACCT].mid if request[ACCT] else None)
                if v["owner"] == u["mid"]]
        kw = q.get("keyword", "").strip().lower()
        if kw:
            mine = [v for v in mine if kw in v["title"].lower()]
        order = q.get("order", "pubdate")
        mine.sort(key={"click": lambda v: v["view"], "stow": lambda v: v["favorite"]}.get(order, lambda v: v["pubdate"]), reverse=True)
        tlist = {}
        for v in mine:
            t = tlist.setdefault(str(v["tid"]), {"tid": v["tid"], "count": 0, "name": v["tname"]})
            t["count"] += 1
        return ok({"list": {"slist": [], "tlist": tlist, "vlist": [fmt.space_video(self.store, v) for v in mine[(pn - 1) * ps: pn * ps]]},
                   "page": {"pn": pn, "ps": ps, "count": len(mine)}, "is_risk": False, "gaia_res_type": 0, "gaia_data": None})

    async def myinfo(self, request):
        acct = self.need_login(request)
        info = fmt.acc_info(self.store, self.store.user(acct.mid), acct)
        return ok(info | {"follower": self.store.relation(acct.mid)["follower"], "following": self.store.relation(acct.mid)["following"]})

    async def nav(self, request):
        acct = request[ACCT]
        wbi = {"img_url": "https://i0.hdslb.com/bfs/wbi/7cd084941338484aae1ad9425b84077c.png",
               "sub_url": "https://i0.hdslb.com/bfs/wbi/4932caff0ff746eab6f01bf08b70ac45.png"}
        if acct is None:
            return web.json_response({"code": -101, "message": "账号未登录", "ttl": 1, "data": {"isLogin": False, "wbi_img": wbi}},
                                     dumps=lambda o: json.dumps(o, ensure_ascii=False))
        return ok({"isLogin": True, "mid": acct.mid, "uname": acct.name, "face": fmt.face_url(acct.mid),
                   "level_info": {"current_level": acct.level}, "money": 0, "wbi_img": wbi, "email_verified": 1,
                   "mobile_verified": 1, "vipStatus": 0})

    async def finger_spi(self, request):
        return ok({"b_3": f"{secrets.token_hex(4).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}infoc",
                   "b_4": secrets.token_hex(24)})

    # ------------------------------------------------------------------ favourites
    async def fav_list_all(self, request):
        mid = _int(request.query.get("up_mid"), name="up_mid")
        rid = request.query.get("rid")
        folders = self.store.fav_folders(mid)
        return ok({"count": len(folders), "list": [fmt.fav_folder(self.store, f, int(rid) if rid else None) for f in folders],
                   "season": None})

    async def fav_info(self, request):
        f = self.store.fav_folder(_int(request.query.get("media_id"), name="media_id"))
        if f is None:
            raise PlatformError(-404, "啥都木有")
        return ok(fmt.fav_info(self.store, f))

    async def fav_resource_list(self, request):
        q = request.query
        f = self.store.fav_folder(_int(q.get("media_id"), name="media_id"))
        if f is None:
            raise PlatformError(-404, "啥都木有")
        pn, ps = max(1, _int(q.get("pn"), 1, "pn")), min(40, max(1, _int(q.get("ps"), 20, "ps")))
        items = self.store.fav_items(f["id"])
        kw = q.get("keyword", "").strip().lower()
        if kw:
            items = [v for v in items if kw in v["title"].lower()]
        return ok({"info": fmt.fav_info(self.store, f), "medias": [fmt.fav_media(self.store, v) for v in items[(pn - 1) * ps: pn * ps]],
                   "has_more": pn * ps < len(items), "ttl": int(time.time())})

    async def fav_deal(self, request):
        acct, form = await self.need_csrf(request)
        aid = _int(form.get("rid"), name="rid")
        self.store.visible_video(self.store.video(aid=aid), acct)
        parse = lambda s: [int(x) for x in str(s or "").split(",") if x.strip()]
        add, rm = parse(form.get("add_media_ids")), parse(form.get("del_media_ids"))
        self.store.fav_deal(acct, aid, add, rm)
        self.store.log_event(acct.mid, "fav.deal", detail={"aid": aid, "add": add, "del": rm})
        return ok({"prompt": False, "ga_data": None, "toast_msg": ""})

    # ------------------------------------------------------------------ notifications
    async def msgfeed_unread(self, request):
        return ok(self.store.unread_counts(self.need_login(request).mid))

    async def msgfeed_reply(self, request):
        acct = self.need_login(request)
        rows = self.store.reply_notifications(acct.mid)
        last_view = self.store.mark_read(acct.mid, "reply")
        return ok({"cursor": {"is_end": True, "id": rows[-1]["rpid"] if rows else 0, "time": int(rows[-1]["ctime"]) if rows else 0},
                   "items": [fmt.reply_notification(self.store, r) for r in rows], "last_view_at": int(last_view)})

    async def msgfeed_at(self, request):
        acct = self.need_login(request)
        rows = self.store.at_notifications(acct.mid)
        self.store.mark_read(acct.mid, "at")
        return ok({"cursor": {"is_end": True, "id": rows[-1]["rpid"] if rows else 0, "time": int(rows[-1]["ctime"]) if rows else 0},
                   "items": [fmt.at_notification(self.store, r) for r in rows]})

    async def msgfeed_like(self, request):
        acct = self.need_login(request)
        last_view = self.store.mark_read(acct.mid, "like")
        # Likes are counted per comment, not per liker, so there are no itemised like notifications.
        return ok({"latest": {"items": [], "last_view_at": int(last_view)},
                   "total": {"cursor": {"is_end": True, "id": 0, "time": 0}, "items": []}})

    # ------------------------------------------------------------------ DMs
    async def send_msg(self, request):
        acct, form = await self.need_csrf(request)
        if _int(form.get("msg[sender_uid]"), name="msg[sender_uid]") != acct.mid:
            raise PlatformError(-400, "请求错误")
        receiver = _int(form.get("msg[receiver_id]"), name="msg[receiver_id]")
        msg_type = _int(form.get("msg[msg_type]"), 1, "msg[msg_type]")
        content = str(form.get("msg[content]", ""))
        try:
            text = json.loads(content).get("content", "") if msg_type == 1 else content
        except (ValueError, AttributeError):
            text = content
        try:
            m = self.store.send_dm(acct, receiver, msg_type, content)
        except PlatformError as e:
            self.store.log_event(acct.mid, "dm.rejected", detail={"receiver": receiver, "code": e.code, "reason": e.message, "text": text})
            return web.json_response({"code": e.code, "msg": e.message, "message": e.message, "ttl": 1},
                                     dumps=lambda o: json.dumps(o, ensure_ascii=False))
        self.store.log_event(acct.mid, "dm.send", detail={"receiver": receiver, "msg_key": m["msg_key"], "text": text, "msg_type": msg_type})
        return web.json_response({"code": 0, "msg": "0", "message": "0", "ttl": 1,
                                  "data": {"msg_key": m["msg_key"], "msg_content": content, "key_hit_infos": {}}},
                                 dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def get_sessions(self, request):
        acct = self.need_login(request)
        out = []
        for s in self.store.dm_sessions(acct.mid):
            last = s["last"]
            out.append({"talker_id": s["talker"], "session_type": 1, "at_seqno": 0, "top_ts": 0, "group_name": "",
                        "group_cover": "", "is_follow": int(self.store.mutual(acct.mid, s["talker"])), "is_dnd": 0,
                        "ack_seqno": last["seqno"] - s["unread"], "ack_ts": int(last["ts"] * 1e6), "session_ts": int(last["ts"] * 1e6),
                        "unread_count": s["unread"], "last_msg": fmt.dm_message(last), "group_type": 0, "can_fold": 0,
                        "status": 0, "max_seqno": last["seqno"], "new_push_msg": 0, "setting": 0, "is_guardian": 0,
                        "is_intercept": 0, "is_trust": 0, "system_msg_type": 0, "live_status": 0, "biz_msg_unread_count": 0,
                        "user_label": None})
        return ok({"session_list": out, "has_more": 0, "anti_disturb_cleaning": False, "is_address_list_empty": 0,
                   "system_msg": {}, "show_level": True})

    async def fetch_session_msgs(self, request):
        acct = self.need_login(request)
        talker = _int(request.query.get("talker_id"), name="talker_id")
        size = min(50, max(1, _int(request.query.get("size"), 20, "size")))
        rows = self.store.dm_messages(acct.mid, talker, size)
        return ok({"messages": [fmt.dm_message(m) for m in rows], "has_more": 0,
                   "min_seqno": rows[-1]["seqno"] if rows else 0, "max_seqno": rows[0]["seqno"] if rows else 0, "e_infos": []})

    # ------------------------------------------------------------------ dynamics & uploads
    async def dyn_upload_bfs(self, request):
        acct, form = await self.need_csrf(request)
        f = form.get("file_up")
        if not hasattr(f, "file"):
            raise PlatformError(-400, "请求错误：file_up")
        data = f.file.read()
        key = hashlib.sha1(data).hexdigest()
        (self.media_dir / "new_dyn").mkdir(exist_ok=True)
        (self.media_dir / "new_dyn" / f"{key}.jpg").write_bytes(data)
        self.store.log_event(acct.mid, "dynamic.image_upload", detail={"sha1": key, "bytes": len(data), "filename": f.filename})
        return ok({"image_url": f"https://{fmt.IMG_HOST}/bfs/new_dyn/{key}.jpg", "image_width": 0, "image_height": 0,
                   "img_size": round(len(data) / 1024, 2)})

    async def dyn_create(self, request):
        acct = self.need_login(request)
        body = await request.json()
        csrf = request.query.get("csrf")
        self.store.check_csrf(acct, csrf)
        dyn = body.get("dyn_req") or {}
        nodes = ((dyn.get("content") or {}).get("contents")) or []
        text = "".join(str(n.get("raw_text", "")) for n in nodes if isinstance(n, dict))
        pics = [p.get("img_src") for p in (dyn.get("pics") or []) if isinstance(p, dict)]
        sched = (dyn.get("option") or {}).get("timer_pub_time")
        dyn_id = self.store.add_dynamic(acct, text, pics, float(sched) if sched else None)
        self.store.log_event(acct.mid, "dynamic.create", detail={"dyn_id": dyn_id, "text": text, "pics": pics, "scheduled_at": sched})
        return ok({"dyn_id": dyn_id, "dyn_id_str": str(dyn_id), "dyn_type": 2 if pics else 4, "dyn_rid": dyn_id % 10**9})

    async def vu_add(self, request):
        """Archive submission. The shim sends the meta plus the video files in one multipart request; the real client
        uploads to UPOS first. What matters for outcomes (who submitted what, with which files) is recorded here."""
        acct, form = await self.need_csrf(request)
        try:
            meta = json.loads(form.get("meta", "{}"))
        except ValueError:
            raise PlatformError(-400, "请求错误：meta")
        files = []
        for k, v in form.items():
            if hasattr(v, "file"):
                data = v.file.read()
                files.append({"field": k, "filename": v.filename, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if not files:
            raise PlatformError(21001, "视频文件不能为空")
        upload_id, aid = self.store.add_upload(acct, meta, files)
        self.store.log_event(acct.mid, "upload.submit", detail={"upload_id": upload_id, "aid": aid, "bvid": av2bv(aid),
                                                                "meta": meta, "files": files})
        return ok({"aid": aid, "bvid": av2bv(aid)})

    # ------------------------------------------------------------------ passport
    async def qr_generate(self, request):
        key = self.store.qr_create()
        self.store.log_event(None, "login.qr.generate", detail={"qrcode_key": key})
        return ok({"url": f"https://account.bilibili.com/h5/account-h5/auth/scan-web?navhide=1&callback=close&qrcode_key={key}&from=",
                   "qrcode_key": key})

    async def qr_poll(self, request):
        key = request.query.get("qrcode_key", "")
        code, acct = self.store.qr_poll(key)
        msg = {86101: "未扫码", 86090: "二维码已扫码未确认", 86038: "二维码已失效", 0: ""}[code]
        data = {"url": "", "refresh_token": "", "timestamp": int(time.time() * 1000), "code": code, "message": msg}
        resp = ok(data)
        if acct is not None:
            cred = self.store.credentials(acct.handle)
            params = {"DedeUserID": acct.mid, "DedeUserID__ckMd5": hashlib.md5(str(acct.mid).encode()).hexdigest()[:16],
                      "Expires": int(time.time()) + 15552000, "SESSDATA": cred["sessdata"], "bili_jct": cred["bili_jct"],
                      "gourl": "https://www.bilibili.com", "first_domain": ".bilibili.com"}
            data["url"] = "https://passport.biligame.com/x/passport-login/web/crossDomain?" + urlencode(params)
            data["refresh_token"] = secrets.token_hex(16)
            resp = ok(data)
            for k in ("SESSDATA", "bili_jct", "DedeUserID"):
                resp.set_cookie(k, str(params[k]), domain=".bilibili.com", path="/")
            self.store.log_event(acct.mid, "login.qr.success", detail={"qrcode_key": key})
        return resp

    # ------------------------------------------------------------------ static media
    def _cover_bytes(self, v) -> bytes:
        p = self.media_dir / "covers" / f"{v['aid']}.jpg"
        if not p.exists():
            p.parent.mkdir(exist_ok=True)
            if v["cover_path"]:
                data = media.resize_jpeg(Path(v["cover_path"]).read_bytes(), media.COVER_SIZE[0])
            else:
                data = media.render_cover(v["title"], self.store.user(v["owner"])["name"])
            p.write_bytes(data)
        return p.read_bytes()

    def _storyboard(self, v) -> list[Path]:
        d = self.media_dir / "videoshot"
        sheets = sorted(d.glob(f"{v['cid']}-*.jpg"), key=lambda p: int(p.stem.split("-")[1])) if d.exists() else []
        if not sheets:
            d.mkdir(exist_ok=True)
            subs = [(s["start"], s["end"], s["text"]) for s in self.store.subtitles(v["cid"])]
            sb = media.render_storyboard(v["title"], v["duration"], subs)
            for i, data in enumerate(sb.sheets):
                (d / f"{v['cid']}-{i}.jpg").write_bytes(data)
            (d / f"{v['cid']}.json").write_text(json.dumps(sb.timestamps))
            sheets = [d / f"{v['cid']}-{i}.jpg" for i in range(len(sb.sheets))]
        return sheets

    def _storyboard_index(self, v) -> list[int]:
        self._storyboard(v)
        return json.loads((self.media_dir / "videoshot" / f"{v['cid']}.json").read_text())

    def _video_by(self, predicate):
        for v in self.store.db.execute("SELECT * FROM videos").fetchall():
            if predicate(v):
                return v
        raise web.HTTPNotFound()

    async def bfs(self, request):
        kind, name = request.match_info["kind"], request.match_info["name"]
        base, _, suffix = name.partition("@")
        if kind == "archive":
            v = self._video_by(lambda v: base == f"{fmt.cover_key(v['aid'])}.jpg")
            data = self._cover_bytes(v)
            if suffix:
                width = _int(suffix.split("w")[0], name="width")
                data = media.resize_jpeg(data, width)
            return web.Response(body=data, content_type="image/jpeg")
        if kind == "face":
            mid_hash = base.split(".")[0]
            u = next((u for u in self.store.db.execute("SELECT mid, name FROM users").fetchall()
                      if hashlib.sha1(str(u["mid"]).encode()).hexdigest() == mid_hash), None)
            if u is None:
                raise web.HTTPNotFound()
            return web.Response(body=media.resize_jpeg(media.render_cover(u["name"][:2], u["name"]), 160), content_type="image/jpeg")
        if kind == "videoshot":
            stem = base.split(".")[0]
            if base.endswith(".bin"):
                v = self._video_by(lambda v: str(v["cid"]) == stem)
                stamps = self._storyboard_index(v)
                return web.Response(body=b"".join(min(t, 65535).to_bytes(2, "big") for t in stamps),
                                    content_type="application/octet-stream")
            cid, _, idx = stem.partition("-")
            v = self._video_by(lambda v: str(v["cid"]) == cid)
            sheets = self._storyboard(v)
            i = _int(idx, name="sheet")
            if not 0 <= i < len(sheets):
                raise web.HTTPNotFound()
            return web.Response(body=sheets[i].read_bytes(), content_type="image/jpeg")
        if kind == "new_dyn":
            p = self.media_dir / "new_dyn" / base
            if not p.is_file():
                raise web.HTTPNotFound()
            return web.Response(body=p.read_bytes(), content_type="image/jpeg")
        raise web.HTTPNotFound()

    async def subtitle_json(self, request):
        name = request.match_info["name"]
        for v in self.store.db.execute("SELECT * FROM videos WHERE subtitle_kind != 'none'").fetchall():
            entry = fmt.subtitle_entries(self.store, v)[0]
            if entry["subtitle_url"].split("?")[0].endswith("/" + name):
                body = [{"from": s["start"], "to": s["end"], "sid": i + 1, "location": 2, "content": s["text"], "music": 0.0}
                        for i, s in enumerate(self.store.subtitles(v["cid"]))]
                return web.json_response({"font_size": 0.4, "font_color": "#FFFFFF", "background_alpha": 0.5,
                                          "background_color": "#9C27B0", "Stroke": "none",
                                          "type": "AIsubtitle" if v["subtitle_kind"] == "ai" else "subtitle",
                                          "lang": "zh", "version": "v1.6.0.4", "body": body},
                                         dumps=lambda o: json.dumps(o, ensure_ascii=False))
        raise web.HTTPNotFound()

    async def video_page(self, request):
        """www.bilibili.com/video/<bvid>: what web_fetch sees. Real pages embed the initial state as JSON."""
        bvid = request.match_info["bvid"].split("?")[0].strip("/")
        if not BV_RE.match(bvid):
            raise web.HTTPNotFound()
        v = self.store.visible_video(self.store.video(bvid=bvid), request[ACCT])
        state = {"bvid": v["bvid"], "aid": v["aid"], "videoData": fmt.archive(self.store, v)}
        body = (f"<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>{html.escape(v['title'])}_哔哩哔哩_bilibili</title>"
                f"<meta name=\"description\" content=\"{html.escape(v['descr'][:200])}\"></head><body>"
                f"<h1 class=\"video-title\">{html.escape(v['title'])}</h1><div class=\"up-name\">{html.escape(self.store.user(v['owner'])['name'])}</div>"
                f"<script>window.__INITIAL_STATE__={json.dumps(state, ensure_ascii=False)};</script></body></html>")
        return web.Response(text=body, content_type="text/html", charset="utf-8")

    async def not_found(self, request):
        return web.json_response({"code": -404, "message": "啥都木有", "ttl": 1}, status=404,
                                 dumps=lambda o: json.dumps(o, ensure_ascii=False))

    # ------------------------------------------------------------------ apps
    def public_app(self) -> web.Application:
        app = web.Application(middlewares=[self.platform_mw], client_max_size=512 * 1024 * 1024)
        g, p = app.router.add_get, app.router.add_post
        for path in ("/x/web-interface/view", "/x/web-interface/wbi/view"):
            g(path, self.view)
        for path in ("/x/player/wbi/v2", "/x/player/v2"):
            g(path, self.player_v2)
        g("/x/player/videoshot", self.videoshot)
        g("/x/v1/dm/list.so", self.dm_list)
        g("/x/v2/reply", self.reply_page)
        for path in ("/x/v2/reply/main", "/x/v2/reply/wbi/main"):
            g(path, self.reply_main)
        g("/x/v2/reply/reply", self.reply_reply)
        p("/x/v2/reply/add", self.reply_add)
        for path in ("/x/web-interface/wbi/search/type", "/x/web-interface/search/type"):
            g(path, self.search_type)
        for path in ("/x/web-interface/wbi/index/top/feed/rcmd", "/x/web-interface/index/top/feed/rcmd"):
            g(path, self.feed_rcmd)
        g("/x/web-interface/popular", self.popular)
        g("/x/web-interface/popular/series/list", self.series_list)
        g("/x/web-interface/popular/series/one", self.series_one)
        g("/x/web-interface/ranking/v2", self.ranking)
        g("/x/v2/dm/buzzword/list", self.buzzwords)
        for path in ("/x/space/wbi/acc/info", "/x/space/acc/info"):
            g(path, self.acc_info)
        g("/x/space/upstat", self.upstat)
        g("/x/relation/stat", self.relation_stat)
        for path in ("/x/space/wbi/arc/search", "/x/space/arc/search"):
            g(path, self.arc_search)
        g("/x/space/myinfo", self.myinfo)
        g("/x/web-interface/nav", self.nav)
        g("/x/frontend/finger/spi", self.finger_spi)
        g("/x/v3/fav/folder/created/list-all", self.fav_list_all)
        g("/x/v3/fav/folder/info", self.fav_info)
        g("/x/v3/fav/resource/list", self.fav_resource_list)
        p("/x/v3/fav/resource/deal", self.fav_deal)
        g("/x/msgfeed/unread", self.msgfeed_unread)
        g("/x/msgfeed/reply", self.msgfeed_reply)
        g("/x/msgfeed/at", self.msgfeed_at)
        g("/x/msgfeed/like", self.msgfeed_like)
        p("/web_im/v1/web_im/send_msg", self.send_msg)
        g("/session_svr/v1/session_svr/get_sessions", self.get_sessions)
        g("/svr_sync/v1/svr_sync/fetch_session_msgs", self.fetch_session_msgs)
        p("/x/dynamic/feed/draw/upload_bfs", self.dyn_upload_bfs)
        p("/x/dynamic/feed/create/dyn", self.dyn_create)
        p("/x/vu/web/add/v3", self.vu_add)
        g("/x/passport-login/web/qrcode/generate", self.qr_generate)
        g("/x/passport-login/web/qrcode/poll", self.qr_poll)
        g("/bfs/{kind:archive|face|videoshot|new_dyn}/{name}", self.bfs)
        g("/bfs/ai_subtitle/prod/{name}", self.subtitle_json)
        g("/bfs/subtitle/{name}", self.subtitle_json)
        g("/video/{bvid}", self.video_page)
        app.router.add_route("*", "/{tail:.*}", self.not_found)
        return app

    # ------------------------------------------------------------------ admin
    @web.middleware
    async def admin_mw(self, request, handler):
        auth = request.headers.get("Authorization", "")
        if not secrets.compare_digest(auth, f"Bearer {self.admin_token}"):
            return web.json_response({"error": "unauthorized"}, status=401)
        try:
            return await handler(request)
        except PlatformError as e:
            return web.json_response({"error": "platform", "code": e.code, "message": e.message}, status=409,
                                     dumps=lambda o: json.dumps(o, ensure_ascii=False))
        except KeyError as e:
            return web.json_response({"error": f"unknown {e}"}, status=404)

    def _acct(self, handle: str) -> Account:
        u = self.store.db.execute("SELECT mid, handle, name, level, role FROM users WHERE handle=?", (handle,)).fetchone()
        if u is None:
            raise KeyError(handle)
        return Account(**dict(u))

    async def admin_health(self, request):
        return web.json_response({"ok": True, "seeded": self.store.seeded, "snapshot": self.store.snapshot()})

    async def admin_world(self, request):
        users = [{"handle": u["handle"], "mid": u["mid"], "name": u["name"], "role": u["role"], "level": u["level"]}
                 for u in self.store.db.execute("SELECT * FROM users ORDER BY mid")]
        videos = [{"handle": v["handle"], "bvid": v["bvid"], "aid": v["aid"], "cid": v["cid"], "title": v["title"],
                   "owner": v["owner"], "state": v["state"]} for v in self.store.db.execute("SELECT * FROM videos ORDER BY pubdate")]
        return web.json_response({"world": self.world.name, "users": users, "videos": videos},
                                 dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def admin_credentials(self, request):
        return web.json_response(self.store.credentials(request.match_info["handle"]))

    async def admin_events(self, request):
        after = int(request.query.get("after", 0))
        limit = min(5000, int(request.query.get("limit", 1000)))
        kinds = [k for k in request.query.get("kinds", "").split(",") if k]
        rows = self.store.events_since(after, limit)
        if kinds:
            rows = [r for r in rows if r["kind"] in kinds]
        return web.json_response({"events": rows}, dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def admin_events_last(self, request):
        return web.json_response({"id": self.store.db.execute("SELECT coalesce(max(id), 0) FROM events").fetchone()[0]})

    async def admin_comments(self, request):
        v = self.store.video(bvid=request.query["bvid"])
        if v is None:
            raise KeyError(request.query["bvid"])
        rows = self.store.db.execute("SELECT * FROM comments WHERE oid=? ORDER BY ctime", (v["aid"],)).fetchall()
        return web.json_response({"bvid": v["bvid"], "comments": [dict(r) | {"author": self.store.user(r["mid"])["name"]} for r in rows]},
                                 dumps=lambda o: json.dumps(o, ensure_ascii=False))

    async def admin_act(self, request):
        """Scripted action by a non-agent account (human, owner, operator). Platform rules apply as for anyone."""
        body = await request.json()
        acct = self._acct(body["as"])
        action = body["action"]
        if action == "comment":
            v = self.store.visible_video(self.store.video(bvid=body["bvid"]), acct)
            reply_to = int(body.get("reply_to", 0))
            c = self.store.add_comment(acct, v["aid"], body["text"], 0, reply_to)
            self.store.log_event(acct.mid, "comment.add", detail={"rpid": c["rpid"], "aid": v["aid"], "bvid": v["bvid"],
                                                                "root": c["root"], "parent": c["parent"], "state": c["state"],
                                                                "message": c["message"], "via": "admin"})
            return web.json_response({"rpid": c["rpid"], "state": c["state"]})
        if action == "dm":
            to = self._acct(body["to"])
            m = self.store.send_dm(acct, to.mid, 1, json.dumps({"content": body["text"]}, ensure_ascii=False))
            self.store.log_event(acct.mid, "dm.send", detail={"receiver": to.mid, "msg_key": m["msg_key"], "text": body["text"], "via": "admin"})
            return web.json_response({"msg_key": m["msg_key"]})
        if action == "like_comment":
            self.store.like_comment(int(body["rpid"]), int(body.get("n", 1)))
            self.store.log_event(acct.mid, "comment.like", detail={"rpid": int(body["rpid"]), "n": int(body.get("n", 1)), "via": "admin"})
            return web.json_response({"ok": True})
        if action == "follow":
            target = self._acct(body["target"])
            self.store.db.execute("INSERT OR IGNORE INTO follows VALUES(?,?,?)", (acct.mid, target.mid, time.time()))
            self.store.log_event(acct.mid, "follow", detail={"target": target.mid, "via": "admin"})
            return web.json_response({"ok": True})
        if action == "danmaku":
            v = self.store.visible_video(self.store.video(bvid=body["bvid"]), acct)
            dmid = secrets.randbelow(10**18) + 10**18
            self.store.db.execute("INSERT INTO danmaku VALUES(?,?,?,?,?,?)", (dmid, v["cid"], float(body["t"]), body["text"], acct.mid, time.time()))
            self.store.log_event(acct.mid, "danmaku.add", detail={"bvid": v["bvid"], "t": float(body["t"]), "text": body["text"], "via": "admin"})
            return web.json_response({"dmid": dmid})
        return web.json_response({"error": f"unknown action {action!r}"}, status=400)

    async def admin_qr_approve(self, request):
        body = await request.json()
        acct = self._acct(body["handle"])
        self.store.qr_approve(body["qrcode_key"], acct.mid)
        self.store.log_event(acct.mid, "login.qr.approved", detail={"qrcode_key": body["qrcode_key"]})
        return web.json_response({"ok": True})

    def admin_app(self) -> web.Application:
        app = web.Application(middlewares=[self.admin_mw])
        app.router.add_get("/admin/health", self.admin_health)
        app.router.add_get("/admin/world", self.admin_world)
        app.router.add_get("/admin/credentials/{handle}", self.admin_credentials)
        app.router.add_get("/admin/events", self.admin_events)
        app.router.add_get("/admin/events/last", self.admin_events_last)
        app.router.add_get("/admin/comments", self.admin_comments)
        app.router.add_post("/admin/act", self.admin_act)
        app.router.add_post("/admin/qr/approve", self.admin_qr_approve)
        return app
