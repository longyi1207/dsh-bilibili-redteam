"""Picture: bytes plus metadata, as used for QR codes, dynamic images and covers."""
from __future__ import annotations

import io
import os

import aiohttp
from PIL import Image


class Picture:
    def __init__(self):
        self.height = 0
        self.width = 0
        self.imageType = ""
        self.size = 0.0
        self.url = ""
        self.content = b""

    def _load(self, content: bytes, url: str) -> "Picture":
        self.content = content
        self.url = url
        img = Image.open(io.BytesIO(content))
        self.width, self.height = img.size
        self.imageType = (img.format or "png").lower()
        self.size = round(len(content) / 1024, 2)
        return self

    @staticmethod
    def from_content(content: bytes, format: str = "png") -> "Picture":
        return Picture()._load(content, f"bytes://{len(content)}")

    @staticmethod
    def from_file(path: str) -> "Picture":
        with open(path, "rb") as f:
            content = f.read()
        return Picture()._load(content, "file://" + os.path.abspath(path))

    @staticmethod
    async def async_from_url(url: str) -> "Picture":
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"Referer": "https://www.bilibili.com"}) as r:
                r.raise_for_status()
                return Picture()._load(await r.read(), url)

    @staticmethod
    def from_url(url: str) -> "Picture":
        import asyncio
        return asyncio.run(Picture.async_from_url(url))

    def convert_format(self, new_format: str) -> "Picture":
        buf = io.BytesIO()
        Image.open(io.BytesIO(self.content)).convert("RGB").save(buf, format=new_format.upper())
        return Picture()._load(buf.getvalue(), self.url)

    def to_file(self, path: str) -> "Picture":
        with open(path, "wb") as f:
            f.write(self.content)
        return self
