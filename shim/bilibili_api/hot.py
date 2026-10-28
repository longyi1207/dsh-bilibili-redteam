"""Popular lists, weekly picks, hot words."""
from __future__ import annotations

from .utils.network import Api

API = "https://api.bilibili.com"


async def get_hot_videos(pn: int = 1, ps: int = 20) -> dict:
    return await Api(f"{API}/x/web-interface/popular", params={"ps": ps, "pn": pn, "web_location": "333.934"}).result


async def get_weekly_hot_videos_list() -> dict:
    return await Api(f"{API}/x/web-interface/popular/series/list", params={"web_location": "333.934"}).result


async def get_weekly_hot_videos(week: int = 1) -> dict:
    return await Api(f"{API}/x/web-interface/popular/series/one", params={"web_location": "333.934", "number": week}).result


async def get_hot_buzzwords(page_num: int = 1, page_size: int = 20) -> dict:
    return await Api(f"{API}/x/v2/dm/buzzword/list", params={"pn": page_num, "ps": page_size, "type_id": 4}).result
