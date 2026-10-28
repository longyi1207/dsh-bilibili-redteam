"""Dynamics (动态): builder and publish."""
from __future__ import annotations

import datetime as dt

from .exceptions import DynamicExceedImagesException
from .utils.network import Api, Credential
from .utils.picture import Picture

API = "https://api.bilibili.com"


async def upload_image(image: Picture, credential: Credential, data: dict | None = None) -> dict:
    credential.raise_for_no_sessdata()
    credential.raise_for_no_bili_jct()
    form = {"biz": "new_dyn", "category": "daily"} | (data or {})
    files = {"file_up": ("image." + (image.imageType or "png"), image.content, f"image/{image.imageType or 'png'}")}
    return await Api(f"{API}/x/dynamic/feed/draw/upload_bfs", "POST", credential=credential, verify=True,
                     data=form, files=files).result


class BuildDynamic:
    def __init__(self):
        self.contents: list[dict] = []
        self.pics: list[Picture] = []
        self.attach_card = None
        self.topic = None
        self.options: dict = {}
        self.time: dt.datetime | None = None

    @staticmethod
    def empty() -> "BuildDynamic":
        return BuildDynamic()

    @staticmethod
    def create_by_args(text: str = "", pics: list | None = None, topic_id: int = -1,
                       send_time: dt.datetime | None = None, **_) -> "BuildDynamic":
        b = BuildDynamic().add_plain_text(text)
        for p in pics or []:
            b.add_image(p)
        if topic_id != -1:
            b.set_topic(topic_id)
        if send_time is not None:
            b.set_send_time(send_time)
        return b

    def add_plain_text(self, text: str) -> "BuildDynamic":
        self.contents.append({"biz_id": "", "type": 1, "raw_text": text})
        return self

    def add_at(self, uid: int) -> "BuildDynamic":
        self.contents.append({"biz_id": str(uid), "type": 2, "raw_text": f"@{uid} "})
        return self

    def add_image(self, image: Picture | list[Picture]) -> "BuildDynamic":
        self.pics += image if isinstance(image, list) else [image]
        if len(self.pics) > 9:
            raise DynamicExceedImagesException()
        return self

    def set_topic(self, topic_id: int) -> "BuildDynamic":
        self.topic = {"id": topic_id}
        return self

    def set_options(self, up_choose_comment: bool = False, close_comment: bool = False) -> "BuildDynamic":
        self.options = {"up_choose_comment": int(up_choose_comment), "close_comment": int(close_comment)}
        return self

    def set_send_time(self, time) -> "BuildDynamic":
        self.time = time if isinstance(time, dt.datetime) else dt.datetime.fromtimestamp(int(time))
        return self


async def send_dynamic(info: BuildDynamic, credential: Credential) -> dict:
    credential.raise_for_no_sessdata()
    credential.raise_for_no_bili_jct()
    pics = []
    for p in info.pics:
        u = await upload_image(p, credential)
        pics.append({"img_src": u["image_url"], "img_width": u["image_width"], "img_height": u["image_height"],
                     "img_size": u["img_size"]})
    option = dict(info.options)
    if info.time is not None:
        option["timer_pub_time"] = int(info.time.timestamp())
    dyn_req = {"content": {"contents": info.contents}, "scene": 2 if pics else 1, "attach_card": info.attach_card,
               "upload_id": f"{credential.dedeuserid}_{int(dt.datetime.now().timestamp())}", "meta": {"app_meta": {"from": "create.dynamic.web", "mobi_app": "web"}},
               "option": option}
    if pics:
        dyn_req["pics"] = pics
    if info.topic:
        dyn_req["topic"] = info.topic
    return await Api(f"{API}/x/dynamic/feed/create/dyn", "POST", credential=credential, verify=True, json_body=True,
                     data={"dyn_req": dyn_req}).result
