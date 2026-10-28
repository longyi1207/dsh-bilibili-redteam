"""Images the platform serves: covers and storyboard sheets (`/x/player/videoshot`).

A world can supply a cover file per video; otherwise the cover is rendered from the title. Storyboard
tiles render the subtitle line on screen at that moment, so `bili_frames` shows the same content the
subtitles carry (and a world can put text into frames on purpose, as a visual channel).

Rendering needs a CJK font. The services image installs Noto CJK; elsewhere set BILISIM_FONT.
"""
from __future__ import annotations

import hashlib
import io
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
)
COVER_SIZE = (1146, 717)
TILE = (480, 270)
SHEET_GRID = (10, 10)
STORYBOARD_STEP_S = 5


def font_path() -> str:
    explicit = os.environ.get("BILISIM_FONT")
    if explicit:
        if not Path(explicit).is_file():
            raise FileNotFoundError(f"BILISIM_FONT={explicit} does not exist")
        return explicit
    for p in FONT_CANDIDATES:
        if Path(p).is_file():
            return p
    raise FileNotFoundError("no CJK font found; install fonts-noto-cjk or set BILISIM_FONT")


def _palette(key: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    h = hashlib.sha256(key.encode()).digest()
    bg = (40 + h[0] % 80, 40 + h[1] % 80, 60 + h[2] % 100)
    return bg, (245, 245, 245)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or draw.textlength(cur + ch, font=font) > width:
            lines.append(cur)
            cur = "" if ch == "\n" else ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def render_cover(title: str, owner: str) -> bytes:
    bg, fg = _palette(title)
    img = Image.new("RGB", COVER_SIZE, bg)
    d = ImageDraw.Draw(img)
    big = ImageFont.truetype(font_path(), 78)
    small = ImageFont.truetype(font_path(), 36)
    y = 150
    for line in _wrap(d, title, big, COVER_SIZE[0] - 160)[:4]:
        d.text((80, y), line, font=big, fill=fg)
        y += 104
    d.text((80, COVER_SIZE[1] - 90), f"@{owner}", font=small, fill=(220, 220, 220))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def resize_jpeg(data: bytes, width: int) -> bytes:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@dataclass
class Storyboard:
    timestamps: list[int]          # seconds, one per tile, across all sheets
    sheets: list[bytes]            # JPEG sheets of SHEET_GRID tiles


def render_storyboard(title: str, duration: int, subtitles: list[tuple[float, float, str]]) -> Storyboard:
    per_sheet = SHEET_GRID[0] * SHEET_GRID[1]
    stamps = list(range(0, max(1, duration), STORYBOARD_STEP_S))
    font = ImageFont.truetype(font_path(), 26)
    small = ImageFont.truetype(font_path(), 18)
    bg, fg = _palette(title)
    sheets = []
    for s in range(0, len(stamps), per_sheet):
        sheet = Image.new("RGB", (TILE[0] * SHEET_GRID[0], TILE[1] * SHEET_GRID[1]), (0, 0, 0))
        for i, t in enumerate(stamps[s:s + per_sheet]):
            tile = Image.new("RGB", TILE, bg)
            d = ImageDraw.Draw(tile)
            d.text((14, 10), title[:24], font=small, fill=(210, 210, 210))
            line = next((txt for a, b, txt in subtitles if a <= t < b), "")
            y = 150
            for ln in _wrap(d, line, font, TILE[0] - 40)[:3]:
                w = d.textlength(ln, font=font)
                d.text(((TILE[0] - w) / 2, y), ln, font=font, fill=fg)
                y += 34
            d.text((TILE[0] - 90, TILE[1] - 30), f"{t // 60:02d}:{t % 60:02d}", font=small, fill=(200, 200, 200))
            sheet.paste(tile, ((i % SHEET_GRID[0]) * TILE[0], (i // SHEET_GRID[0]) * TILE[1]))
        buf = io.BytesIO()
        sheet.save(buf, format="JPEG", quality=80)
        sheets.append(buf.getvalue())
    return Storyboard(stamps, sheets)
