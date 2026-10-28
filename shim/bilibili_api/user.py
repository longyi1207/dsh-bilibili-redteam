"""User space: profile, stats, uploads."""
from __future__ import annotations

from enum import Enum

from .utils.network import Api, Credential

API = "https://api.bilibili.com"


class VideoOrder(Enum):
    PUBDATE = "pubdate"
    FAVORITE = "stow"
    VIEW = "click"


class User:
    def __init__(self, uid: int, credential: Credential | None = None):
        self.__uid = uid
        self.credential = credential if credential is not None else Credential()

    def get_uid(self) -> int:
        return self.__uid

    async def get_user_info(self) -> dict:
        return await Api(f"{API}/x/space/wbi/acc/info", credential=self.credential, params={"mid": self.__uid}).result

    async def get_up_stat(self) -> dict:
        return await Api(f"{API}/x/space/upstat", credential=self.credential, params={"mid": self.__uid}).result

    async def get_relation_info(self) -> dict:
        return await Api(f"{API}/x/relation/stat", credential=self.credential, params={"vmid": self.__uid}).result

    async def get_videos(self, tid: int = 0, pn: int = 1, ps: int = 30, keyword: str = "",
                         order: VideoOrder = VideoOrder.PUBDATE) -> dict:
        params = {"mid": self.__uid, "ps": ps, "tid": tid, "pn": pn, "keyword": keyword, "order": order.value,
                  "platform": "web"}
        return await Api(f"{API}/x/space/wbi/arc/search", credential=self.credential, params=params).result


async def get_self_info(credential: Credential) -> dict:
    return await Api(f"{API}/x/space/myinfo", credential=credential, verify=True).result
