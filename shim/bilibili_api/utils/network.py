"""Credential and the request/response contract of bilibili-api-python's `Api`.

Contract reproduced (checked against bilibili_api/utils/network.py, 17.4.2):
  * endpoints marked as needing login raise CredentialNoSessdataException without SESSDATA;
  * non-GET requests raise CredentialNoBiliJctException without bili_jct, and carry csrf/csrf_token;
  * HTTP status != 200 -> NetworkException(status, body);
  * JSON `code` != 0 -> ResponseCodeException(code, msg or message, raw);
  * otherwise the `data` field (or `result`) is returned.
Not reproduced: WBI signing, buvid/bili_ticket fetching, the shared per-loop client. They change no
response the plugin reads.
"""
from __future__ import annotations

import json
from typing import Any

import aiohttp

from ..exceptions import (CredentialNoBiliJctException, CredentialNoBuvid3Exception, CredentialNoDedeUserIDException,
                          CredentialNoSessdataException, NetworkException, ResponseCodeException)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Referer": "https://www.bilibili.com",
}
TIMEOUT = aiohttp.ClientTimeout(total=30)


class Credential:
    def __init__(self, sessdata: str | None = None, bili_jct: str | None = None, buvid3: str | None = None,
                 buvid4: str | None = None, dedeuserid: str | None = None, ac_time_value: str | None = None):
        self.sessdata = "" if sessdata is None else (sessdata if "%" in sessdata else sessdata.replace(",", "%2C").replace("*", "%2A"))
        self.bili_jct = bili_jct or ""
        self.buvid3 = buvid3 or ""
        self.buvid4 = buvid4 or ""
        self.dedeuserid = dedeuserid or ""
        self.ac_time_value = ac_time_value or ""

    def get_cookies(self) -> dict:
        return {"SESSDATA": self.sessdata, "buvid3": self.buvid3, "buvid4": self.buvid4, "bili_jct": self.bili_jct,
                "ac_time_value": self.ac_time_value, "DedeUserID": self.dedeuserid}

    def has_sessdata(self) -> bool:
        return bool(self.sessdata)

    def has_bili_jct(self) -> bool:
        return bool(self.bili_jct)

    def has_dedeuserid(self) -> bool:
        return bool(self.dedeuserid)

    def raise_for_no_sessdata(self):
        if not self.sessdata:
            raise CredentialNoSessdataException()

    def raise_for_no_bili_jct(self):
        if not self.bili_jct:
            raise CredentialNoBiliJctException()

    def raise_for_no_buvid3(self):
        if not self.buvid3:
            raise CredentialNoBuvid3Exception()

    def raise_for_no_dedeuserid(self):
        if not self.dedeuserid:
            raise CredentialNoDedeUserIDException()

    async def check_valid(self) -> bool:
        try:
            data = await Api("https://api.bilibili.com/x/web-interface/nav", credential=self).result
            return bool(data and data.get("isLogin"))
        except ResponseCodeException:
            return False


class Api:
    def __init__(self, url: str, method: str = "GET", *, credential: Credential | None = None, verify: bool = False,
                 no_csrf: bool = False, json_body: bool = False, params: dict | None = None, data: dict | None = None,
                 files: dict | None = None, ignore_code: bool = False):
        self.url, self.method = url, method.upper()
        self.credential = credential if credential is not None else Credential()
        self.verify, self.no_csrf, self.json_body, self.ignore_code = verify, no_csrf, json_body, ignore_code
        self.params = dict(params or {})
        self.data = dict(data or {})
        self.files = dict(files or {})

    def update_params(self, **kw) -> "Api":
        self.params.update(kw)
        return self

    def update_data(self, **kw) -> "Api":
        self.data.update(kw)
        return self

    @staticmethod
    def _clean(d: dict) -> dict:
        return {k: (int(v) if isinstance(v, bool) else v) for k, v in d.items() if v is not None}

    @property
    async def result(self) -> Any:
        return await self.request()

    async def request(self, raw: bool = False, byte: bool = False) -> Any:
        if self.verify:
            self.credential.raise_for_no_sessdata()
        if self.method != "GET" and not self.no_csrf:
            self.credential.raise_for_no_bili_jct()
        params, data = self._clean(self.params), self._clean(self.data)
        if not self.no_csrf and self.verify and self.method in ("POST", "DELETE", "PATCH"):
            if self.json_body:
                params["csrf"] = self.credential.bili_jct
            else:
                data["csrf"] = self.credential.bili_jct
                data["csrf_token"] = self.credential.bili_jct
        cookies = {k: v for k, v in self.credential.get_cookies().items() if v}
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
        headers = dict(HEADERS)
        if cookie_header:
            headers["Cookie"] = cookie_header
        kwargs: dict[str, Any] = {"params": {k: str(v) for k, v in params.items()}, "headers": headers}
        if self.method != "GET":
            if self.json_body:
                kwargs["json"] = data
            elif self.files:
                form = aiohttp.FormData()
                for k, v in data.items():
                    form.add_field(k, str(v))
                for k, (filename, content, ctype) in self.files.items():
                    form.add_field(k, content, filename=filename, content_type=ctype)
                kwargs["data"] = form
            else:
                kwargs["data"] = {k: str(v) for k, v in data.items()}
        async with aiohttp.ClientSession(timeout=TIMEOUT) as s:
            async with s.request(self.method, self.url, **kwargs) as resp:
                body = await resp.read()
                if resp.status != 200:
                    raise NetworkException(resp.status, body.decode("utf-8", "replace"))
                if byte:
                    return body
        text = body.decode("utf-8", "replace")
        if not text:
            return None
        resp_data = json.loads(text)
        if raw:
            return resp_data
        if not self.ignore_code:
            code = resp_data.get("code")
            if code is None:
                raise ResponseCodeException(-1, "API 返回数据未含 code 字段", resp_data)
            if code != 0:
                msg = resp_data.get("msg")
                if msg is None:
                    msg = resp_data.get("message")
                if msg is None:
                    msg = "接口未返回错误信息"
                raise ResponseCodeException(code, msg, resp_data)
        real = resp_data.get("data")
        return real if real is not None else resp_data.get("result")


def get(url: str, *, credential: Credential | None = None, verify: bool = False, **params) -> Api:
    return Api(url, "GET", credential=credential, verify=verify, params=params)


def post(url: str, *, credential: Credential | None = None, verify: bool = True, data: dict | None = None,
         json_body: bool = False, files: dict | None = None, no_csrf: bool = False) -> Api:
    return Api(url, "POST", credential=credential, verify=verify, data=data, json_body=json_body, files=files, no_csrf=no_csrf)
