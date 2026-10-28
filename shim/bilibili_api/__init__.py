"""Sandbox stand-in for bilibili-api-python 17.4.x, covering what dsh-bili-scroll uses.

Every call goes to Bilibili's real hostnames, which resolve to the bili-sandbox simulator inside the
sandbox network. See shim/README.md for the covered surface and known differences.
"""
import asyncio

from . import comment, dynamic, favorite_list, homepage, hot, opus, rank, search, session, user, video
from .exceptions import (ApiException, ArgsException, CredentialNoBiliJctException, CredentialNoSessdataException,
                         NetworkException, ResponseCodeException, StatementException)
from .utils.network import Credential

__version__ = "17.4.2+bilisandbox"
BILISANDBOX_SHIM = True


def sync(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    raise RuntimeError(f"sync() called inside a running event loop ({loop!r}); await the coroutine instead")
