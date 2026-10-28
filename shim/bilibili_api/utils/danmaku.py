"""Danmaku objects as returned by Video.get_danmakus (attribute names match bilibili-api-python)."""
from __future__ import annotations

import time
from enum import Enum


class DmMode(Enum):
    FLY = 1
    TOP = 5
    BOTTOM = 4
    REVERSE = 6
    SPECIAL = 9


class DmFontSize(Enum):
    EXTREME_SMALL = 12
    SUPER_SMALL = 16
    SMALL = 18
    NORMAL = 25
    BIG = 36
    SUPER_BIG = 45
    EXTREME_BIG = 64


class Danmaku:
    def __init__(self, text: str, dm_time: float = 0.0, send_time: float | None = None, crc32_id: str = "",
                 color: str = "ffffff", weight: int = -1, id_: int = -1, id_str: str = "", action: str = "",
                 mode: int = DmMode.FLY.value, font_size: int = DmFontSize.NORMAL.value, is_sub: bool = False,
                 pool: int = 0, attr: int = -1, uid: int = -1):
        self.text = text
        self.dm_time = dm_time
        self.send_time = time.time() if send_time is None else send_time
        self.crc32_id = crc32_id
        self.color = color
        self.weight = weight
        self.id_ = id_
        self.id_str = id_str
        self.action = action
        self.mode = mode
        self.font_size = font_size
        self.is_sub = is_sub
        self.pool = pool
        self.attr = attr
        self.uid = uid

    def __str__(self):
        return f"{self.text}, {self.dm_time}"
