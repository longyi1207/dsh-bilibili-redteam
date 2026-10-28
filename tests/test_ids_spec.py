import pytest
import yaml

from bili_sandbox.world.ids import av2bv, bv2av
from bili_sandbox.world.spec import WorldSpecError, load_world, parse_offset

from conftest import WORLD


@pytest.mark.parametrize("aid,bvid", [(111298867365120, "BV1L9Uoa9EUx"), (170001, "BV17x411w7KC"), (2, "BV1xx411c7mD")])
def test_av_bv_vectors(aid, bvid):
    assert av2bv(aid) == bvid
    assert bv2av(bvid) == aid


def test_offsets():
    assert parse_offset("-2d") == -172800
    assert parse_offset("-90m") == -5400
    with pytest.raises(WorldSpecError):
        parse_offset("+1d")
    with pytest.raises(WorldSpecError):
        parse_offset("tomorrow")


def test_e2e_world_loads_deterministically():
    a, b = load_world(WORLD), load_world(WORLD)
    assert [v.bvid for v in a.videos.values()] == [v.bvid for v in b.videos.values()]
    assert len({u.mid for u in a.users.values()}) == len(a.users)
    assert a.users["fish_a"].role == "agent"


def test_world_rejects_dangling_handles(tmp_path):
    raw = yaml.safe_load(WORLD.read_text())
    raw["videos"][0]["comments"][0]["by"] = "nobody"
    p = tmp_path / "w.yaml"
    p.write_text(yaml.safe_dump(raw, allow_unicode=True))
    with pytest.raises(WorldSpecError, match="unknown user handle"):
        load_world(p)


def test_world_rejects_unknown_keys(tmp_path):
    raw = yaml.safe_load(WORLD.read_text())
    raw["videos"][0]["views"] = 3
    p = tmp_path / "w.yaml"
    p.write_text(yaml.safe_dump(raw, allow_unicode=True))
    with pytest.raises(WorldSpecError, match="unknown keys"):
        load_world(p)
