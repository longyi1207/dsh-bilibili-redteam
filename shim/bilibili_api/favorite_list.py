"""Video favourite folders.

Mirrors bilibili-api-python 17.4.x exactly in what exists: there is no `FavoriteListResource`, and
`FavoriteList.get_info()` requires a media_id. The plugin's lib/favops.py calls both in a way that fails
against the real library too, so auto-favouriting fails the same way here.
"""
from __future__ import annotations

from enum import Enum

from .exceptions import StatementException
from .utils.network import Api, Credential

API = "https://api.bilibili.com"


class FavoriteListContentOrder(Enum):
    MTIME = "mtime"
    VIEW = "view"
    PUBTIME = "pubtime"


class FavoriteListType(Enum):
    VIDEO = "video"
    ARTICLE = "articles"
    CHEESE = "pugvfav"


class SearchFavoriteListMode(Enum):
    ONLY = 0
    ALL = 1


class FavoriteList:
    def __init__(self, type_: FavoriteListType = FavoriteListType.VIDEO, media_id: int | None = None,
                 credential: Credential | None = None):
        self.__type = type_
        self.__media_id = media_id
        self.credential = credential if credential else Credential()

    def is_video_favorite_list(self) -> bool:
        return self.__type == FavoriteListType.VIDEO

    def get_media_id(self) -> int | None:
        return self.__media_id

    def get_favorite_list_type(self) -> FavoriteListType:
        return self.__type

    async def get_info(self) -> dict:
        if self.__media_id is None:
            raise StatementException("视频收藏夹需要 media_id")
        return await Api(f"{API}/x/v3/fav/folder/info", credential=self.credential, params={"media_id": self.__media_id}).result

    async def get_content_video(self, page: int = 1, keyword: str | None = None,
                                order: FavoriteListContentOrder = FavoriteListContentOrder.MTIME, tid: int = 0,
                                mode: SearchFavoriteListMode = SearchFavoriteListMode.ONLY) -> dict:
        if self.__type != FavoriteListType.VIDEO:
            raise StatementException("此函数仅在收藏夹为视频收藏家时可用")
        return await get_video_favorite_list_content(self.__media_id, page, keyword, order, tid, mode, self.credential)

    async def get_content(self, page: int = 1) -> dict:
        return await self.get_content_video(page)


async def get_video_favorite_list(uid: int, video=None, credential: Credential | None = None) -> dict:
    params = {"up_mid": uid, "type": 2, "web_location": "333.1387"}
    if video is not None:
        params["rid"] = video.get_aid()
    return await Api(f"{API}/x/v3/fav/folder/created/list-all", credential=credential, params=params).result


async def get_video_favorite_list_content(media_id: int, page: int = 1, keyword: str | None = None,
                                          order: FavoriteListContentOrder = FavoriteListContentOrder.MTIME, tid: int = 0,
                                          mode: SearchFavoriteListMode = SearchFavoriteListMode.ONLY,
                                          credential: Credential | None = None) -> dict:
    params = {"media_id": media_id, "pn": page, "ps": 20, "order": order.value, "tid": tid, "type": mode.value,
              "platform": "web", "web_location": "333.1387"}
    if keyword is not None:
        params["keyword"] = keyword
    return await Api(f"{API}/x/v3/fav/resource/list", credential=credential, params=params).result
