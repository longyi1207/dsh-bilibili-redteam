"""Video: info, subtitles, danmaku, storyboard snapshots."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from .exceptions import ArgsException
from .utils.aid_bvid_transformer import aid2bvid, bvid2aid
from .utils.danmaku import Danmaku
from .utils.network import Api, Credential

API = "https://api.bilibili.com"


class Video:
    def __init__(self, bvid: str | None = None, aid: int | None = None, credential: Credential | None = None):
        if bvid is not None:
            self.set_bvid(bvid)
        elif aid is not None:
            self.set_aid(aid)
        else:
            raise ArgsException("请至少提供 bvid 和 aid 中的其中一个参数。")
        self.credential = credential if credential is not None else Credential()
        self.__info = None

    def set_bvid(self, bvid: str) -> None:
        if not re.search("^BV[a-zA-Z0-9]{10}$", bvid):
            raise ArgsException("bvid 提供错误，必须是以 BV 开头的纯字母和数字组成的 12 位字符串（大小写敏感）。")
        self.__bvid = bvid
        self.__aid = bvid2aid(bvid)

    def get_bvid(self) -> str:
        return self.__bvid

    def set_aid(self, aid: int) -> None:
        if aid <= 0:
            raise ArgsException("aid 不能小于或等于 0。")
        self.__aid = aid
        self.__bvid = aid2bvid(aid)

    def get_aid(self) -> int:
        return self.__aid

    async def get_info(self) -> dict:
        resp = await Api(f"{API}/x/web-interface/view", credential=self.credential,
                         params={"bvid": self.__bvid, "aid": self.__aid}).result
        self.__info = resp
        return resp

    async def _info(self) -> dict:
        return self.__info if self.__info is not None else await self.get_info()

    async def get_pages(self) -> list:
        return (await self._info())["pages"]

    async def get_cid(self, page_index: int) -> int:
        if page_index < 0:
            raise ArgsException("分 p 号必须大于或等于 0。")
        pages = await self.get_pages()
        if page_index >= len(pages):
            raise ArgsException("不存在该分 p。")
        return pages[page_index]["cid"]

    async def get_player_info(self, cid: int | None = None, epid: int | None = None) -> dict:
        if cid is None:
            raise ArgsException("cid 不能为空")
        params = {"aid": self.__aid, "cid": cid, "isGaiaAvoided": False, "web_location": 1315873}
        if epid is not None:
            params["epid"] = epid
        return await Api(f"{API}/x/player/wbi/v2", credential=self.credential, verify=True, params=params).result

    async def get_subtitle(self, cid: int | None = None) -> dict:
        if cid is None:
            cid = await self.get_cid(0)
        return (await self.get_player_info(cid=cid)).get("subtitle")

    async def get_danmakus(self, page_index: int = 0, date=None, cid: int | None = None,
                           from_seg: int | None = None, to_seg: int | None = None) -> list[Danmaku]:
        if cid is None:
            cid = await self.get_cid(page_index)
        params = {"oid": cid, "type": 1, "pid": self.__aid}
        if date is not None:
            self.credential.raise_for_no_sessdata()
            params["date"] = date.strftime("%Y-%m-%d")
        raw = await Api(f"{API}/x/v1/dm/list.so", credential=self.credential, params=params).request(byte=True)
        out = []
        for d in ET.fromstring(raw.decode("utf-8")).iter("d"):
            p = d.attrib.get("p", "").split(",")
            out.append(Danmaku(text=d.text or "", dm_time=float(p[0]), mode=int(p[1]), font_size=int(p[2]),
                               color=format(int(p[3]), "06x"), send_time=float(p[4]), pool=int(p[5]), crc32_id=p[6],
                               id_=int(p[7]), id_str=p[7], weight=int(p[8]) if len(p) > 8 else -1))
        return out

    async def get_video_snapshot(self, cid: int | None = None, json_index: bool = False, pvideo: bool = True) -> dict:
        params: dict = {"aid": self.__aid}
        if not pvideo:
            params["bvid"] = self.__bvid
            if json_index:
                params["index"] = 1
            if cid is not None:
                params["cid"] = cid
        return await Api(f"{API}/x/player/videoshot", credential=self.credential, params=params).result

    async def set_favorite(self, add_media_ids: list[int] = [], del_media_ids: list[int] = []) -> dict:
        data = {"rid": self.__aid, "type": 2, "add_media_ids": ",".join(map(str, add_media_ids)),
                "del_media_ids": ",".join(map(str, del_media_ids))}
        return await Api(f"{API}/x/v3/fav/resource/deal", "POST", credential=self.credential, verify=True, data=data).result
