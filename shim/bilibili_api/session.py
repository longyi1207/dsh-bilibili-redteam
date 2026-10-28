"""Private messages and notification feeds."""
from __future__ import annotations

import json
from enum import Enum

from .exceptions import ApiException
from .utils.network import Api, Credential

API = "https://api.bilibili.com"
VC = "https://api.vc.bilibili.com"


class EventType(Enum):
    TEXT = 1
    PICTURE = 2
    WITHDRAW = 5
    GROUPS_PICTURE = 6
    SHARE_VIDEO = 7
    NOTICE = 10
    PUSHED_VIDEO = 11


async def send_msg(credential: Credential, receiver_id: int, msg_type: EventType, content) -> dict:
    credential.raise_for_no_sessdata()
    credential.raise_for_no_bili_jct()
    if credential.has_dedeuserid() and int(credential.dedeuserid) != 0:
        sender_uid = int(credential.dedeuserid)
    else:
        from .user import get_self_info
        sender_uid = (await get_self_info(credential))["mid"]
    if msg_type == EventType.TEXT:
        real_content = json.dumps({"content": content})
    elif msg_type == EventType.WITHDRAW:
        real_content = str(content)
    else:
        raise ApiException("信息类型不支持。")
    data = {"msg[sender_uid]": sender_uid, "msg[receiver_id]": receiver_id, "msg[receiver_type]": 1,
            "msg[msg_type]": msg_type.value, "msg[msg_status]": 0, "msg[content]": real_content,
            "msg[dev_id]": "A6716E9A-7CE3-47AF-994B-F0B34178D28D", "msg[new_face_version]": 0,
            "msg[timestamp]": int(__import__("time").time()), "from_firework": 0, "build": 0, "mobi_app": "web"}
    return await Api(f"{VC}/web_im/v1/web_im/send_msg", "POST", credential=credential, verify=True, data=data).result


async def get_sessions(credential: Credential, session_type: int = 4) -> dict:
    params = {"session_type": session_type, "group_fold": 1, "unfollow_fold": 0, "sort_rule": 2, "build": 0, "mobi_app": "web"}
    return await Api(f"{VC}/session_svr/v1/session_svr/get_sessions", credential=credential, verify=True, params=params).result


async def fetch_session_msgs(talker_id: int, credential: Credential, session_type: int = 1, begin_seqno: int = 0) -> dict:
    params = {"talker_id": talker_id, "session_type": session_type, "begin_seqno": begin_seqno, "size": 20,
              "build": 0, "mobi_app": "web"}
    return await Api(f"{VC}/svr_sync/v1/svr_sync/fetch_session_msgs", credential=credential, verify=True, params=params).result


async def get_unread_messages(credential: Credential) -> dict:
    return await Api(f"{API}/x/msgfeed/unread", credential=credential, verify=True).result


async def get_replies(credential: Credential, last_reply_id: int | None = None, reply_time: int | None = None) -> dict:
    return await Api(f"{API}/x/msgfeed/reply", credential=credential, verify=True,
                     params={"id": last_reply_id, "reply_time": reply_time}).result


async def get_likes(credential: Credential, last_id: int | None = None, like_time: int | None = None) -> dict:
    return await Api(f"{API}/x/msgfeed/like", credential=credential, verify=True,
                     params={"id": last_id, "like_time": like_time}).result


async def get_at(credential: Credential, last_id: int | None = None, at_time: int | None = None) -> dict:
    return await Api(f"{API}/x/msgfeed/at", credential=credential, verify=True,
                     params={"id": last_id, "at_time": at_time}).result
