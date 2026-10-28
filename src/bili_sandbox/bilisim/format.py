"""Render world rows as Bilibili API payloads.

Field names and nesting follow the live web API as documented by SocialSisterYi/bilibili-API-collect
and as read by the code under test (the plugin's `mcp_server.py`, `lib/dm.mjs`, `lib/verify.mjs`).
Fields the code under test never reads are kept where they are cheap and stable, so a model that
dumps a raw payload sees a familiar shape.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timedelta, timezone

from ..world.store import WorldStore

IMG_HOST = "i0.hdslb.com"
BJT = timezone(timedelta(hours=8))


def face_url(mid: int) -> str:
    return f"https://{IMG_HOST}/bfs/face/{hashlib.sha1(str(mid).encode()).hexdigest()}.jpg"


def cover_key(aid: int) -> str:
    return hashlib.sha1(f"cover:{aid}".encode()).hexdigest()


def pic_url(aid: int) -> str:
    # The view API returns covers as plain http:// (measured by the plugin author, 10/10); the plugin upgrades them.
    return f"http://{IMG_HOST}/bfs/archive/{cover_key(aid)}.jpg"


def mmss(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def time_desc(ts: float) -> str:
    d = time.time() - ts
    if d < 60:
        return "刚刚发布"
    if d < 3600:
        return f"{int(d // 60)}分钟前发布"
    if d < 86400:
        return f"{int(d // 3600)}小时前发布"
    return datetime.fromtimestamp(ts, BJT).strftime("%Y-%m-%d") + "发布"


def owner(store: WorldStore, mid: int) -> dict:
    u = store.user(mid)
    return {"mid": mid, "name": u["name"] if u else "", "face": face_url(mid)}


def member(store: WorldStore, mid: int) -> dict:
    u = store.user(mid)
    return {"mid": str(mid), "uname": u["name"], "sex": "保密", "sign": u["sign"], "avatar": face_url(mid), "rank": "10000",
            "face_nft_new": 0, "is_senior_member": 0,
            "level_info": {"current_level": u["level"], "current_min": 0, "current_exp": 0, "next_exp": 0},
            "pendant": {"pid": 0, "name": "", "image": ""}, "nameplate": {"nid": 0, "name": "", "image": ""},
            "official_verify": {"type": -1, "desc": ""}, "vip": {"vipType": 0, "vipStatus": 0}}


def stat(store: WorldStore, v) -> dict:
    c = store.counts(v["aid"], v["cid"])
    return {"aid": v["aid"], "view": v["view"], "danmaku": c["danmaku"], "reply": c["reply"], "favorite": v["favorite"],
            "coin": v["coin"], "share": v["share"], "now_rank": 0, "his_rank": 0, "like": v["like_count"], "dislike": 0,
            "evaluation": "", "vt": 0}


def subtitle_entries(store: WorldStore, v) -> list[dict]:
    if v["subtitle_kind"] == "none":
        return []
    ai = v["subtitle_kind"] == "ai"
    sid = int(hashlib.sha1(f"sub:{v['cid']}".encode()).hexdigest()[:15], 16)
    lan = "ai-zh" if ai else "zh-CN"
    key = hashlib.sha1(f"subkey:{v['cid']}".encode()).hexdigest()
    url = (f"//aisubtitle.hdslb.com/bfs/ai_subtitle/prod/{v['aid']}{v['cid']}{key[:32]}?auth_key={int(time.time()) + 1800}-{key[32:40]}-0-{key[:8]}"
           if ai else f"//aisubtitle.hdslb.com/bfs/subtitle/{key}.json")
    return [{"id": sid, "lan": lan, "lan_doc": "中文（自动生成）" if ai else "中文（中国）", "is_lock": False,
             "subtitle_url": url, "type": 1 if ai else 0, "id_str": str(sid), "ai_type": 0 if ai else None,
             "ai_status": 2 if ai else None}]


def archive(store: WorldStore, v) -> dict:
    """The `view` payload, also the element type of popular / ranking lists."""
    return {"bvid": v["bvid"], "aid": v["aid"], "videos": 1, "tid": v["tid"], "tname": v["tname"], "copyright": 1,
            "pic": pic_url(v["aid"]), "title": v["title"], "pubdate": int(v["pubdate"]), "ctime": int(v["pubdate"]),
            "desc": v["descr"], "desc_v2": [{"raw_text": v["descr"], "type": 1, "biz_id": 0}], "state": 0,
            "duration": v["duration"], "rights": {"bp": 0, "elec": 0, "download": 1, "movie": 0, "pay": 0, "hd5": 1,
                                                   "no_reprint": 1, "autoplay": 1, "ugc_pay": 0, "is_cooperation": 0},
            "owner": owner(store, v["owner"]), "stat": stat(store, v), "dynamic": "", "cid": v["cid"],
            "dimension": {"width": 1920, "height": 1080, "rotate": 0},
            "pages": [{"cid": v["cid"], "page": 1, "from": "vupload", "part": v["title"], "duration": v["duration"],
                       "vid": "", "weblink": "", "dimension": {"width": 1920, "height": 1080, "rotate": 0}}],
            "subtitle": {"allow_submit": False, "list": subtitle_entries(store, v)},
            "short_link_v2": f"https://b23.tv/{v['bvid']}", "is_upower_exclusive": False}


def comment(store: WorldStore, c, viewer, with_preview: bool = True) -> dict:
    rc = store.reply_count(c["rpid"], viewer) if c["root"] == 0 else 0
    d = {"rpid": c["rpid"], "oid": c["oid"], "type": c["type"], "mid": c["mid"], "root": c["root"], "parent": c["parent"],
         "dialog": c["parent"] if c["root"] else 0, "count": rc, "rcount": rc, "state": 0, "fansgrade": 0, "attr": 0,
         "ctime": int(c["ctime"]), "mid_str": str(c["mid"]), "oid_str": str(c["oid"]), "rpid_str": str(c["rpid"]),
         "root_str": str(c["root"]), "parent_str": str(c["parent"]), "dialog_str": str(c["parent"] if c["root"] else 0),
         "like": c["like_count"], "action": 0, "member": member(store, c["mid"]),
         "content": {"message": c["message"], "members": [], "jump_url": {}, "max_line": 6},
         "replies": None, "up_action": {"like": False, "reply": False}, "invisible": False,
         "reply_control": {"max_line": 6, "time_desc": time_desc(c["ctime"])}}
    if with_preview and c["root"] == 0 and rc:
        d["replies"] = [comment(store, r, viewer, with_preview=False) for r in store.replies(c["rpid"], viewer)[:3]]
    return d


def search_item(store: WorldStore, v, keyword: str, score: float) -> dict:
    title = v["title"]
    for term in sorted({t for t in keyword.split() if t}, key=len, reverse=True):
        idx = title.lower().find(term.lower())
        if idx >= 0:
            title = title[:idx] + '<em class="keyword">' + title[idx:idx + len(term)] + "</em>" + title[idx + len(term):]
    c = store.counts(v["aid"], v["cid"])
    u = store.user(v["owner"])
    return {"type": "video", "id": v["aid"], "author": u["name"], "mid": v["owner"], "typeid": str(v["tid"]),
            "typename": v["tname"], "arcurl": f"http://www.bilibili.com/video/av{v['aid']}", "aid": v["aid"],
            "bvid": v["bvid"], "title": title, "description": v["descr"], "arcrank": "0",
            "pic": f"//{IMG_HOST}/bfs/archive/{cover_key(v['aid'])}.jpg", "play": v["view"], "video_review": c["danmaku"],
            "favorites": v["favorite"], "tag": ",".join(json.loads(v["tags"])), "review": c["reply"],
            "pubdate": int(v["pubdate"]), "senddate": int(v["pubdate"]), "duration": mmss(v["duration"]),
            "badgepay": False, "hit_columns": ["title"], "view_type": "", "is_pay": 0, "is_union_video": 0,
            "rank_score": int(score * 1000)}


def search_page(items: list[dict], page: int, page_size: int, total: int) -> dict:
    return {"seid": str(int(time.time() * 1000)), "page": page, "pagesize": page_size, "numResults": total,
            "numPages": max(1, math.ceil(total / page_size)), "suggest_keyword": "", "rqt_type": "search",
            "cost_time": {}, "exp_list": {}, "egg_hit": 0, "result": items, "show_column": 0,
            "in_black_key": 0, "in_white_key": 0}


def user_search_item(store: WorldStore, u) -> dict:
    n_videos = sum(1 for v in store.videos() if v["owner"] == u["mid"])
    return {"type": "bili_user", "mid": u["mid"], "uname": u["name"], "usign": u["sign"],
            "fans": store.relation(u["mid"])["follower"], "videos": n_videos, "upic": face_url(u["mid"]),
            "level": u["level"], "gender": 3, "is_upuser": int(n_videos > 0), "is_live": 0, "room_id": 0,
            "official_verify": {"type": -1, "desc": ""}, "hit_columns": ["uname"]}


def rcmd_reason(v) -> dict:
    if v["like_count"] >= 10000:
        return {"content": f"{v['like_count'] // 10000}万点赞", "reason_type": 1}
    return {"reason_type": 0}


def feed_item(store: WorldStore, v, pos: int) -> dict:
    c = store.counts(v["aid"], v["cid"])
    return {"id": v["aid"], "bvid": v["bvid"], "cid": v["cid"], "goto": "av",
            "uri": f"https://www.bilibili.com/video/{v['bvid']}", "pic": pic_url(v["aid"]).replace("http://", "https://"),
            "pic_4_3": pic_url(v["aid"]).replace("http://", "https://"), "title": v["title"], "duration": v["duration"],
            "pubdate": int(v["pubdate"]), "owner": owner(store, v["owner"]),
            "stat": {"view": v["view"], "like": v["like_count"], "danmaku": c["danmaku"], "vt": 0},
            "av_feature": None, "is_followed": 0, "rcmd_reason": rcmd_reason(v), "show_info": 1,
            "track_id": f"web_pegasus_{pos}.{int(time.time())}", "pos": pos, "room_info": None, "ogv_info": None,
            "business_info": None, "is_stock": 0, "enable_vt": 0, "vt_display": "", "dislike_switch": 1}


def acc_info(store: WorldStore, u, viewer) -> dict:
    followed = bool(viewer and store.db.execute("SELECT 1 FROM follows WHERE follower=? AND followee=?",
                                                (viewer.mid, u["mid"])).fetchone())
    return {"mid": u["mid"], "name": u["name"], "sex": "保密", "face": face_url(u["mid"]), "face_nft": 0, "face_nft_type": 0,
            "sign": u["sign"], "rank": 10000, "level": u["level"], "jointime": 0, "moral": 0, "silence": 0, "coins": 0,
            "fans_badge": False, "official": {"role": 0, "title": "", "desc": "", "type": -1},
            "vip": {"type": 0, "status": 0, "due_date": 0}, "pendant": {"pid": 0, "name": "", "image": ""},
            "nameplate": {"nid": 0, "name": "", "image": ""}, "is_followed": followed,
            "top_photo": "http://i1.hdslb.com/bfs/space/cb1c3ef50e22b6096fde67febe863494caefebad.png",
            "birthday": "", "live_room": None, "is_senior_member": 0}


def space_video(store: WorldStore, v) -> dict:
    c = store.counts(v["aid"], v["cid"])
    u = store.user(v["owner"])
    return {"comment": c["reply"], "typeid": v["tid"], "play": v["view"], "pic": pic_url(v["aid"]), "subtitle": "",
            "description": v["descr"], "copyright": "1", "title": v["title"], "review": 0, "author": u["name"],
            "mid": v["owner"], "created": int(v["pubdate"]), "length": f"{v['duration'] // 60:02d}:{v['duration'] % 60:02d}",
            "video_review": c["danmaku"], "aid": v["aid"], "bvid": v["bvid"], "hide_click": False, "is_pay": 0,
            "is_union_video": 0, "is_steins_gate": 0, "is_live_playback": 0, "meta": None, "is_avoided": 0,
            "attribute": 0, "is_charging_arc": False, "vt": 0, "enable_vt": 0, "vt_display": "", "playback_position": 0}


def fav_folder(store: WorldStore, f, rid: int | None = None) -> dict:
    fav_state = 0
    if rid is not None:
        fav_state = int(bool(store.db.execute("SELECT 1 FROM fav_items WHERE folder=? AND aid=?", (f["id"], rid)).fetchone()))
    return {"id": f["id"], "fid": f["id"], "mid": f["mid"], "attr": f["attr"], "title": f["title"],
            "fav_state": fav_state, "media_count": f["media_count"]}


def fav_info(store: WorldStore, f) -> dict:
    return {"id": f["id"], "fid": f["id"], "mid": f["mid"], "attr": f["attr"], "title": f["title"], "cover": "",
            "upper": {"mid": f["mid"], "name": store.user(f["mid"])["name"], "face": face_url(f["mid"]), "followed": False},
            "cover_type": 2, "cnt_info": {"collect": 0, "play": 0, "thumb_up": 0, "share": 0}, "type": 11, "intro": "",
            "ctime": int(f["ctime"]), "mtime": int(f["ctime"]), "state": 0, "fav_state": 0, "like_state": 0,
            "media_count": f["media_count"]}


def fav_media(store: WorldStore, v) -> dict:
    c = store.counts(v["aid"], v["cid"])
    return {"id": v["aid"], "type": 2, "title": v["title"], "cover": pic_url(v["aid"]), "intro": v["descr"], "page": 1,
            "duration": v["duration"], "upper": {"mid": v["owner"], "name": store.user(v["owner"])["name"],
                                                 "face": face_url(v["owner"])},
            "attr": 0, "cnt_info": {"collect": v["favorite"], "play": v["view"], "danmaku": c["danmaku"], "vt": 0},
            "link": f"bilibili://video/{v['aid']}", "ctime": int(v["pubdate"]), "pubtime": int(v["pubdate"]),
            "fav_time": int(v["fav_time"]), "bv_id": v["bvid"], "bvid": v["bvid"], "season": None, "ogv": None,
            "ugc": {"first_cid": v["cid"]}}


def dm_message(m) -> dict:
    return {"sender_uid": m["sender"], "receiver_type": 1, "receiver_id": m["receiver"], "msg_type": m["msg_type"],
            "content": m["content"], "msg_seqno": m["seqno"], "timestamp": int(m["ts"]), "at_uids": [0],
            "msg_key": m["msg_key"], "msg_status": 0, "notify_code": "", "new_face_version": 0}


def reply_notification(store: WorldStore, c) -> dict:
    v = store.video(aid=c["oid"])
    u = store.user(c["mid"])
    return {"id": c["rpid"], "user": {"mid": c["mid"], "fans": 0, "nickname": u["name"], "avatar": face_url(c["mid"]),
                                      "mid_link": "", "follow": False},
            "item": {"subject_id": c["oid"], "root_id": c["root"], "source_id": c["rpid"], "target_id": c["parent"],
                     "type": "reply", "business_id": 1, "business": "评论", "title": v["title"] if v else "",
                     "desc": "", "image": pic_url(c["oid"]) if v else "",
                     "uri": f"https://www.bilibili.com/video/{v['bvid']}" if v else "",
                     "native_uri": f"bilibili://video/{c['oid']}", "detail_title": "", "root_reply_content": "",
                     "source_content": c["message"], "target_reply_content": c["parent_message"] if "parent_message" in c.keys() else "",
                     "at_details": [], "topic_details": [], "hide_reply_button": False, "hide_like_button": False,
                     "like_state": 0, "danmu": None, "message": ""},
            "counts": 1, "is_multi": 0, "reply_time": int(c["ctime"])}


def at_notification(store: WorldStore, c) -> dict:
    v = store.video(aid=c["oid"])
    u = store.user(c["mid"])
    return {"id": c["rpid"], "user": {"mid": c["mid"], "fans": 0, "nickname": u["name"], "avatar": face_url(c["mid"]),
                                      "mid_link": "", "follow": False},
            "item": {"type": "reply", "business": "评论", "business_id": 1, "title": v["title"] if v else "",
                     "image": "", "uri": f"https://www.bilibili.com/video/{v['bvid']}" if v else "",
                     "source_content": c["message"], "source_id": c["rpid"], "target_id": c["parent"],
                     "root_id": c["root"], "native_url": "", "at_details": []},
            "at_time": int(c["ctime"])}
