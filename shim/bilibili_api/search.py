"""Search by type (videos, users)."""
from __future__ import annotations

from enum import Enum

from .utils.network import Api

API = "https://api.bilibili.com"


class SearchObjectType(Enum):
    VIDEO = "video"
    BANGUMI = "media_bangumi"
    FT = "media_ft"
    LIVE = "live"
    ARTICLE = "article"
    TOPIC = "topic"
    USER = "bili_user"
    LIVEUSER = "live_user"
    PHOTO = "photo"


class OrderVideo(Enum):
    TOTALRANK = "totalrank"
    CLICK = "click"
    PUBDATE = "pubdate"
    DM = "dm"
    STOW = "stow"
    SCORES = "scores"


class OrderUser(Enum):
    FANS = "fans"
    LEVEL = "level"


async def search_by_type(keyword: str, search_type: SearchObjectType | None = None, order_type=None,
                         time_range: int = -1, video_zone_type=None, order_sort: int | None = None,
                         category_id=None, time_start: str | None = None, time_end: str | None = None,
                         page: int = 1, page_size: int = 42, debug_param_func=None) -> dict:
    params: dict = {"keyword": keyword, "page": page, "page_size": page_size}
    if search_type is not None:
        params["search_type"] = search_type.value
    if order_type is not None:
        params["order"] = order_type.value
    if order_sort is not None:
        params["order_sort"] = order_sort
    if time_start is not None:
        params["pubtime_begin_s"] = time_start
    if time_end is not None:
        params["pubtime_end_s"] = time_end
    if debug_param_func:
        debug_param_func(params)
    return await Api(f"{API}/x/web-interface/wbi/search/type", params=params).result
