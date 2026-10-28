"""Archive upload. The real client pre-uploads chunks to UPOS and then submits; the shim submits meta and the
page files in one multipart request to the simulator's `member.bilibili.com/x/vu/web/add/v3`, which records
who uploaded which bytes with which metadata. Event names follow the real uploader's coarse phases."""
from __future__ import annotations

import json
import os
from enum import Enum

from .exceptions import ApiException, ArgsException
from .utils.network import Api, Credential
from .utils.picture import Picture


class Lines(Enum):
    BDA2 = "bda2"
    QN = "qn"
    WS = "ws"
    BLDSA = "bldsa"


class VideoUploaderEvents(Enum):
    PREUPLOAD = "PREUPLOAD"
    PRE_PAGE = "PRE_PAGE"
    AFTER_PAGE = "AFTER_PAGE"
    PRE_SUBMIT = "PRE_SUBMIT"
    AFTER_SUBMIT = "AFTER_SUBMIT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VideoUploaderPage:
    def __init__(self, path: str, title: str, description: str = ""):
        self.path, self.title, self.description = path, title, description

    def get_size(self) -> int:
        return os.path.getsize(self.path)


class VideoMeta:
    def __init__(self, tid: int, title: str, desc: str, cover: Picture | str, tags: list[str] | str, topic: int | None = None,
                 mission_id: int | None = None, original: bool = True, source: str | None = None, recreate: bool = False,
                 no_reprint: bool = False, open_elec: bool = False, up_selection_reply: bool = False,
                 up_close_danmu: bool = False, up_close_reply: bool = False, lossless_music: bool = False,
                 dolby: bool = False, subtitle: dict | None = None, dynamic: str | None = None,
                 neutral_mark: str | None = None, delay_time: int | None = None, porder=None):
        if isinstance(tags, str):
            tags = tags.split(",")
        if not tags:
            raise ArgsException("tags 不能为空")
        if len(title) > 80:
            raise ArgsException("title 不能超过 80 字")
        if not original and not source:
            raise ArgsException("转载视频需要提供 source")
        self.tid, self.title, self.desc, self.cover, self.tags = tid, title, desc, cover, tags
        self.extra = {"topic": topic, "mission_id": mission_id, "original": original, "source": source, "recreate": recreate,
                      "no_reprint": no_reprint, "open_elec": open_elec, "dynamic": dynamic, "delay_time": delay_time}

    def to_dict(self) -> dict:
        return {"tid": self.tid, "title": self.title, "desc": self.desc, "tags": self.tags,
                "copyright": 1 if self.extra["original"] else 2, **{k: v for k, v in self.extra.items() if v is not None}}


class VideoUploader:
    def __init__(self, pages: list[VideoUploaderPage], meta: VideoMeta | dict, credential: Credential,
                 cover: Picture | str | None = None, line: Lines | None = None):
        self.pages, self.meta, self.credential, self.cover, self.line = pages, meta, credential, cover, line
        self._handlers: dict[str, list] = {}

    def on(self, event: str):
        def deco(fn):
            self._handlers.setdefault(event, []).append(fn)
            return fn
        return deco

    async def _dispatch(self, name: str, data) -> None:
        for fn in self._handlers.get(name, []) + self._handlers.get("__ALL__", []):
            res = fn({"name": name, "data": data})
            if hasattr(res, "__await__"):
                await res

    async def start(self) -> dict:
        self.credential.raise_for_no_sessdata()
        self.credential.raise_for_no_bili_jct()
        meta = self.meta.to_dict() if isinstance(self.meta, VideoMeta) else dict(self.meta)
        cover = self.cover or (self.meta.cover if isinstance(self.meta, VideoMeta) else None)
        files = {}
        await self._dispatch(VideoUploaderEvents.PREUPLOAD.value, {"pages": len(self.pages)})
        for i, page in enumerate(self.pages):
            await self._dispatch(VideoUploaderEvents.PRE_PAGE.value, {"page": i, "path": page.path})
            with open(page.path, "rb") as f:
                files[f"page{i}"] = (os.path.basename(page.path), f.read(), "video/mp4")
            meta.setdefault("pages", []).append({"title": page.title, "desc": page.description})
            await self._dispatch(VideoUploaderEvents.AFTER_PAGE.value, {"page": i})
        if isinstance(cover, Picture):
            files["cover"] = ("cover." + (cover.imageType or "png"), cover.content, f"image/{cover.imageType or 'png'}")
        await self._dispatch(VideoUploaderEvents.PRE_SUBMIT.value, meta)
        try:
            result = await Api("https://member.bilibili.com/x/vu/web/add/v3", "POST", credential=self.credential,
                               verify=True, data={"meta": json.dumps(meta, ensure_ascii=False)}, files=files).result
        except ApiException as e:
            await self._dispatch(VideoUploaderEvents.FAILED.value, {"err": str(e)})
            raise
        await self._dispatch(VideoUploaderEvents.AFTER_SUBMIT.value, result)
        await self._dispatch(VideoUploaderEvents.COMPLETED.value, result)
        return result
