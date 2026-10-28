"""Figures for the README / report, from a sweep's results.csv (aggregate numbers only).

    uv run python scripts/make_figures.py runs/sweeps/<sweep>/results.csv docs/figures

Palette: two categorical slots (blue = plugin 0.1.7, orange = plugin 2.3.0), validated for colour-vision deficiency
(adjacent CVD dE 24.7, normal-vision dE 33.6, both >= 3:1 on the light surface). Error bars are 95% Wilson intervals.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
SERIES = {"0.1.7": "#2a78d6", "2.3.0": "#eb6834"}
LABEL = {"0.1.7": "plugin 0.1.7 (surge-era; shell + filesystem)", "2.3.0": "plugin 2.3.0 (current; minimal profile)"}
CATS = [("benign", "benign\n(10 videos)"), ("doom", "AI doom\n(2)"), ("human_critical", "humans are\nselfish (2)"),
        ("ai_identity", "AI identity /\nsolidarity (2)"), ("injection", "addresses AI\nagents (4)")]


def wilson(k: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, p - max(0.0, c - h)), max(0.0, min(1.0, c + h) - p)


def style(ax, title: str, subtitle: str) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold", pad=40)
    ax.text(0, 1.085, subtitle, transform=ax.transAxes, fontsize=9, color=INK2)


def grouped(ax, groups: list[str], values: dict[str, list[tuple[int, int]]], ylabel: str, ymax: float = 1.0) -> None:
    width = 0.36
    for i, (pl, ks) in enumerate(values.items()):
        xs = [g + (i - 0.5) * (width + 0.02) for g in range(len(groups))]
        stats = [wilson(k, n) for k, n in ks]
        ax.bar(xs, [s[0] for s in stats], width, color=SERIES[pl], label=LABEL[pl], edgecolor=SURFACE, linewidth=1.5)
        ax.errorbar(xs, [s[0] for s in stats], yerr=[[s[1] for s in stats], [s[2] for s in stats]], fmt="none",
                    ecolor=INK2, elinewidth=1, capsize=0)
        for x, (k, n), s in zip(xs, ks, stats):
            ax.text(x, s[0] + s[2] + 0.02, f"{k}/{n}", ha="center", va="bottom", fontsize=7.5, color=INK2)
    ax.set_xticks(range(len(groups)), groups, fontsize=9, color=INK)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_ylabel(ylabel, fontsize=9, color=INK2)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, labelcolor=INK,
              borderaxespad=0.2, handlelength=1.2)


def main(csv_path: Path, out: Path) -> None:
    rows = list(csv.DictReader(csv_path.open()))
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    num = lambda r, k: int(float(r[k] or 0))

    # 1. what the agents recommended to their owner, by content category
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=SURFACE)
    choice = {pl: [next(((num(r, "picked_of_read"), num(r, "read")) for r in rows if r["table"] == "choice" and r["plugin"] == pl
                         and r["category"] == c), (0, 0)) for c, _ in CATS] for pl in SERIES}
    grouped(ax, [lab for _, lab in CATS], choice, "picked for the owner's report / videos read", ymax=0.85)
    style(ax, "Agents keep value-laden and agent-addressed content out of their owners' reports",
          "Share of videos an agent read that it then recommended (a headed entry in the daily report). 216 rounds; bars: 95% CI.")
    fig.tight_layout()
    fig.savefig(out / "choice.png", dpi=160, facecolor=SURFACE)

    # 2. injection videos: flagged to the owner (complied is zero everywhere)
    inj = [("INJ_COMMENT", "post a code word\nin a comment"), ("INJ_DM", "DM the owner a\ncode word"),
           ("INJ_STOP", "stop work, write\na fixed report"), ("INJ_LEAK", "post the owner's\nemail + project code")]
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=SURFACE)
    flagged = {pl: [next(((num(r, "flagged"), num(r, "exposed")) for r in rows if r["table"] == "injection" and r["plugin"] == pl
                          and r["canary_id"] == cid), (0, 0)) for cid, _ in inj] for pl in SERIES}
    complied = sum(num(r, "complied") for r in rows if r["table"] == "injection")
    exposed = sum(num(r, "exposed") for r in rows if r["table"] == "injection")
    grouped(ax, [lab for _, lab in inj], flagged, "warned the owner / rounds exposed", ymax=1.0)
    style(ax, f"Injected instructions: {complied} of {exposed} exposures obeyed",
          "Bars: exposures after which the agent explicitly called it a prompt injection to its owner (keyword match; a lower bound).")
    fig.tight_layout()
    fig.savefig(out / "injection.png", dpi=160, facecolor=SURFACE)

    # 3. routing around the tool whitelist (pooled over peer conditions)
    stages = [("recon", "searched the plugin's\nsource for write functions"), ("attempt", "ran a script that\ncalls one"),
              ("executed", "a platform write happened\nwith no tool for it")]
    fig, ax = plt.subplots(figsize=(9, 4.4), facecolor=SURFACE)
    byp = {pl: [(sum(num(r, st) for r in rows if r["table"] == "bypass" and r["plugin"] == pl),
                 sum(num(r, "rounds") for r in rows if r["table"] == "bypass" and r["plugin"] == pl)) for st, _ in stages]
           for pl in SERIES}
    grouped(ax, [lab for _, lab in stages], byp, "share of duty rounds", ymax=0.7)
    style(ax, "With a shell, the surge-era agent routes around its tool whitelist on its own",
          "No adversary needed: the model wanted to DM its owner, found the DM tool withheld, and called the function directly.")
    fig.tight_layout()
    fig.savefig(out / "bypass.png", dpi=160, facecolor=SURFACE)
    print("wrote", sorted(p.name for p in out.glob("*.png")))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
