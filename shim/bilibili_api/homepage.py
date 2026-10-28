"""Home recommendation feed."""
from __future__ import annotations

from .utils.network import Api, Credential


async def get_videos(credential: Credential | None = None) -> dict:
    return await Api("https://api.bilibili.com/x/web-interface/wbi/index/top/feed/rcmd", credential=credential).result
