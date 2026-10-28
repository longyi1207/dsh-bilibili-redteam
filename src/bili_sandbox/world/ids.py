"""Bilibili id conventions: av <-> BV conversion (the post-2020 algorithm with 51-bit aids).

Reference implementation: SocialSisterYi/bilibili-API-collect, docs/misc/bvid_desc.md.
Test vector from that page: av111298867365120 <-> BV1L9Uoa9EUx.
"""
from __future__ import annotations

import re

XOR_CODE = 23442827791579
MASK_CODE = 2251799813685247
MAX_AID = 1 << 51
ALPHABET = "FcwAPNKTMug3GV5Lj7EJnHpWsx4tb8haYeviqBz6rkCy12mUSDQX9RdoZf"
ENCODE_MAP = (8, 7, 0, 5, 1, 3, 2, 4, 6)
BASE = 58
BV_RE = re.compile(r"^BV1[0-9A-Za-z]{9}$")


def av2bv(aid: int) -> str:
    if not 0 < aid < MAX_AID:
        raise ValueError(f"aid out of range: {aid}")
    chars = [""] * 9
    tmp = (MAX_AID | aid) ^ XOR_CODE
    for pos in ENCODE_MAP:
        chars[pos] = ALPHABET[tmp % BASE]
        tmp //= BASE
    return "BV1" + "".join(chars)


def bv2av(bvid: str) -> int:
    if not BV_RE.match(bvid):
        raise ValueError(f"not a BV id: {bvid!r}")
    body = bvid[3:]
    tmp = 0
    for pos in reversed(ENCODE_MAP):
        tmp = tmp * BASE + ALPHABET.index(body[pos])
    return (tmp & MASK_CODE) ^ XOR_CODE
