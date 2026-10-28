"""av <-> BV conversion (same algorithm as the simulator's world/ids.py)."""
XOR_CODE = 23442827791579
MASK_CODE = 2251799813685247
MAX_AID = 1 << 51
ALPHABET = "FcwAPNKTMug3GV5Lj7EJnHpWsx4tb8haYeviqBz6rkCy12mUSDQX9RdoZf"
ENCODE_MAP = (8, 7, 0, 5, 1, 3, 2, 4, 6)
BASE = 58


def aid2bvid(aid: int) -> str:
    chars = [""] * 9
    tmp = (MAX_AID | aid) ^ XOR_CODE
    for pos in ENCODE_MAP:
        chars[pos] = ALPHABET[tmp % BASE]
        tmp //= BASE
    return "BV1" + "".join(chars)


def bvid2aid(bvid: str) -> int:
    body = bvid[3:]
    tmp = 0
    for pos in reversed(ENCODE_MAP):
        tmp = tmp * BASE + ALPHABET.index(body[pos])
    return (tmp & MASK_CODE) ^ XOR_CODE
