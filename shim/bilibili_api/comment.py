"""Comment areas: list and post."""
from __future__ import annotations

import json
from enum import Enum

from .exceptions import ArgsException
from .utils.network import Api, Credential

API = "https://api.bilibili.com"


class CommentResourceType(Enum):
    VIDEO = 1
    ARTICLE = 12
    DYNAMIC_DRAW = 11
    DYNAMIC = 17
    AUDIO = 14
    AUDIO_LIST = 19
    CHEESE = 33
    BLACK_ROOM = 6
    MANGA = 22


class OrderType(Enum):
    LIKE = 2
    TIME = 0


async def get_comments(oid: int, type_: CommentResourceType, page_index: int = 1, order: OrderType = OrderType.TIME,
                       credential: Credential | None = None) -> dict:
    if page_index <= 0:
        raise ArgsException("page_index 必须大于或等于 1")
    params = {"pn": page_index, "type": type_.value, "oid": oid, "sort": order.value}
    return await Api(f"{API}/x/v2/reply", credential=credential, params=params).result


async def send_comment(text: str, oid: int, type_: CommentResourceType, root: int | None = None,
                       parent: int | None = None, credential: Credential | None = None, pic=None) -> dict:
    if credential is None:
        credential = Credential()
    credential.raise_for_no_sessdata()
    credential.raise_for_no_bili_jct()
    data = {"oid": oid, "type": type_.value, "message": text, "plat": 1,
            "statistics": json.dumps({"appId": 100, "platform": 5}), "gaia_source": "main_web"}
    if root is not None and parent is None:
        data["root"] = root
        data["parent"] = root
    elif root is not None and parent is not None:
        data["root"] = root
        data["parent"] = parent
    elif root is None and parent is not None:
        raise ArgsException("root 不能为空")
    if pic is not None:
        from .dynamic import upload_image
        pics = pic if isinstance(pic, list) else [pic]
        uploaded = [await upload_image(p, credential) for p in pics]
        data["pictures"] = json.dumps([{"img_src": u["image_url"], "img_width": u["image_width"],
                                        "img_height": u["image_height"], "img_size": u["img_size"]} for u in uploaded])
    return await Api(f"{API}/x/v2/reply/add", "POST", credential=credential, verify=True, data=data).result


class Comment:
    def __init__(self, oid: int, type_: CommentResourceType, rpid: int, credential: Credential | None = None):
        self.oid, self.type_, self.rpid = oid, type_, rpid
        self.credential = credential if credential else Credential()

    async def get_sub_comments(self, page_index: int = 1, page_size: int = 10) -> dict:
        params = {"pn": page_index, "ps": page_size, "type": self.type_.value, "oid": self.oid, "root": self.rpid}
        return await Api(f"{API}/x/v2/reply/reply", credential=self.credential, params=params).result
