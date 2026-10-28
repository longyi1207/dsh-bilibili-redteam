import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shim"))  # the shim is imported as `bilibili_api` in contract tests
WORLD = ROOT / "worlds" / "e2e_smoke.yaml"
