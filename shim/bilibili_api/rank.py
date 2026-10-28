"""Ranking lists. PGC (bangumi/film) rankings are not simulated and answer -404 like an unknown endpoint."""
from __future__ import annotations

from enum import Enum

from .utils.network import Api

API = "https://api.bilibili.com"


class RankDayType(Enum):
    THREE_DAY = 3
    WEEK = 7


class RankType(Enum):
    All = {"api_type": "x", "rid": 0, "type": "all"}
    Bangumi = {"api_type": "pgc", "season_type": 1}
    GuochuangAnime = {"api_type": "pgc", "season_type": 4}
    Guochuang = {"api_type": "x", "rid": 168, "type": "all"}
    Documentary = {"api_type": "pgc", "season_type": 3}
    Douga = {"api_type": "x", "rid": 1005, "type": "all"}
    Music = {"api_type": "x", "rid": 1003, "type": "all"}
    Dance = {"api_type": "x", "rid": 1004, "type": "all"}
    Game = {"api_type": "x", "rid": 1008, "type": "all"}
    Knowledge = {"api_type": "x", "rid": 1010, "type": "all"}
    Technology = {"api_type": "x", "rid": 1012, "type": "all"}
    Sports = {"api_type": "x", "rid": 1018, "type": "all"}
    Car = {"api_type": "x", "rid": 1013, "type": "all"}
    Life = {"api_type": "x", "rid": 160, "type": "all"}
    Food = {"api_type": "x", "rid": 1020, "type": "all"}
    Animal = {"api_type": "x", "rid": 1024, "type": "all"}
    Kichiku = {"api_type": "x", "rid": 1007, "type": "all"}
    Fashion = {"api_type": "x", "rid": 1014, "type": "all"}
    Ent = {"api_type": "x", "rid": 1002, "type": "all"}
    Cinephile = {"api_type": "x", "rid": 1001, "type": "all"}
    Movie = {"api_type": "pgc", "season_type": 2}
    TV = {"api_type": "pgc", "season_type": 5}
    Variety = {"api_type": "pgc", "season_type": 7}
    Original = {"api_type": "x", "rid": 0, "type": "origin"}
    Rookie = {"api_type": "x", "rid": 0, "type": "rookie"}


async def get_rank(type_: RankType = RankType.All, day: RankDayType = RankDayType.THREE_DAY) -> dict:
    params: dict = {"web_location": "333.934"}
    if type_.value["api_type"] == "x":
        params["rid"] = type_.value["rid"]
        params["type"] = type_.value["type"]
        url = f"{API}/x/web-interface/ranking/v2"
    else:
        params["season_type"] = type_.value["season_type"]
        params["day"] = day.value
        url = f"{API}/pgc/season/rank/web/list"
    return await Api(url, params=params).result
