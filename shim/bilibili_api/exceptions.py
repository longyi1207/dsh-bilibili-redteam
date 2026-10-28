"""Exception types with the same names and user-visible messages as bilibili-api-python 17.x.

mcp_server.py returns `str(e)` to the model in many tools, so the text matters for fidelity.
"""


class ApiException(Exception):
    def __init__(self, msg: str = "出现了错误，但是未说明具体原因。"):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class ArgsException(ApiException):
    pass


class StatementException(ApiException):
    pass


class ResponseCodeException(ApiException):
    def __init__(self, code: int, msg: str, raw: dict | None = None):
        super().__init__(msg)
        self.code = code
        self.raw = raw

    def __str__(self):
        return f"接口返回错误代码：{self.code}，信息：{self.msg}。\n{self.raw}"


class NetworkException(ApiException):
    def __init__(self, status: int, msg: str):
        super().__init__(msg)
        self.status = status
        self.msg = f"网络错误，状态码：{status} - {msg}。"

    def __str__(self):
        return self.msg


class _CredentialMissing(ApiException):
    field = ""

    def __init__(self):
        super().__init__(f"Credential 类未提供 {self.field} 或者为空。")


class CredentialNoSessdataException(_CredentialMissing):
    field = "sessdata"


class CredentialNoBiliJctException(_CredentialMissing):
    field = "bili_jct"


class CredentialNoBuvid3Exception(_CredentialMissing):
    field = "buvid3"


class CredentialNoDedeUserIDException(_CredentialMissing):
    field = "DedeUserID"


class DynamicExceedImagesException(ApiException):
    def __init__(self):
        super().__init__("最多上传 9 张图片")
