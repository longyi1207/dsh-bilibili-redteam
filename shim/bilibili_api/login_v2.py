"""QR-code login (web channel). Private attribute names match the real class: mcp_server.py reads
`_QrCodeLogin__qr_link`. Approval of a pending code is done from the simulator's admin API."""
from __future__ import annotations

import enum
import io
import os
import tempfile

import qrcode

from .exceptions import ArgsException
from .utils.network import Api, Credential
from .utils.picture import Picture

PASSPORT = "https://passport.bilibili.com"


class QrCodeLoginChannel(enum.Enum):
    WEB = "web"
    TV = "tv"


class QrCodeLoginEvents(enum.Enum):
    SCAN = "scan"
    CONF = "confirm"
    TIMEOUT = "timeout"
    DONE = "done"


class QrCodeLogin:
    def __init__(self, platform: QrCodeLoginChannel = QrCodeLoginChannel.WEB) -> None:
        if platform != QrCodeLoginChannel.WEB:
            raise ArgsException("沙盒只提供网页端扫码登录")
        self.__platform = platform
        self.__qr_link = ""
        self.__qr_key = ""
        self.__qr_picture: Picture | None = None
        self.__qr_terminal = ""
        self.__credential: Credential | None = None

    def has_qrcode(self) -> bool:
        return self.__qr_picture is not None

    def has_done(self) -> bool:
        return self.__credential is not None

    def get_credential(self) -> Credential:
        if self.__credential is None:
            raise ArgsException("登录未完成")
        return self.__credential

    def get_qrcode_picture(self) -> Picture:
        if self.__qr_picture is None:
            raise ArgsException("二维码尚未生成")
        return self.__qr_picture

    def get_qrcode_terminal(self) -> str:
        return self.__qr_terminal

    async def generate_qrcode(self) -> None:
        data = await Api(f"{PASSPORT}/x/passport-login/web/qrcode/generate", credential=Credential(),
                         params={"source": "main-fe-header"}).result
        self.__qr_link = data["url"]
        self.__qr_key = data["qrcode_key"]
        qr = qrcode.QRCode()
        qr.add_data(self.__qr_link)
        img_path = os.path.join(tempfile.gettempdir(), "qrcode.png")
        qr.make_image().save(img_path)
        self.__qr_picture = Picture.from_file(img_path)
        buf = io.StringIO()
        qr.print_ascii(out=buf)
        self.__qr_terminal = buf.getvalue()

    async def check_state(self) -> QrCodeLoginEvents:
        events = await Api(f"{PASSPORT}/x/passport-login/web/qrcode/poll", credential=Credential(),
                           params={"qrcode_key": self.__qr_key, "source": "main-fe-header"}).result
        code = events["code"]
        if code == 86101:
            return QrCodeLoginEvents.SCAN
        if code == 86090:
            return QrCodeLoginEvents.CONF
        if code == 86038:
            return QrCodeLoginEvents.TIMEOUT
        fields = dict(kv.split("=", 1) for kv in events["url"].split("?", 1)[1].split("&"))
        self.__credential = Credential(sessdata=fields.get("SESSDATA", ""), bili_jct=fields.get("bili_jct", ""),
                                       dedeuserid=fields.get("DedeUserID", ""), ac_time_value=events.get("refresh_token", ""))
        return QrCodeLoginEvents.DONE
