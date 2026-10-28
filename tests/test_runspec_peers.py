import pytest
import yaml

from bili_sandbox.runspec import PeerAction, SpecError, load_experiment

from conftest import WORLD


def _world_with_operator(tmp_path):
    w = yaml.safe_load(WORLD.read_text())
    w["users"].append({"handle": "op", "name": "脚本账号", "level": 4, "role": "operator"})
    p = tmp_path / "w.yaml"
    p.write_text(yaml.safe_dump(w, allow_unicode=True))
    return p


def _experiment(tmp_path, peers):
    world = _world_with_operator(tmp_path)
    exp = {"run": {"name": "t", "world": str(world), "budget_usd": 1},
           "agents": [{"id": "a", "account": "fish_a", "owner": "owner_a", "dsh": "0.2.1-rc.2", "plugin": "2.3.0"}],
           "peers": peers}
    p = tmp_path / "e.yaml"
    p.write_text(yaml.safe_dump(exp, allow_unicode=True))
    return p


@pytest.mark.parametrize("spec,wave,expected", [("1", 1, True), ("1", 2, False), (">=2", 1, False), (">=2", 3, True), ("all", 9, True)])
def test_wave_matching(spec, wave, expected):
    assert PeerAction("op", spec, "comment", "x").applies(wave) is expected


def test_valid_peers_load(tmp_path):
    peers = [{"account": "op", "actions": [
        {"waves": "1", "type": "comment", "video": "cot", "text": "hi", "likes": 5, "label": "c1"},
        {"waves": "1", "type": "reply", "to_label": "c1", "text": "re"},
        {"waves": ">=2", "type": "reply_to_agent_comments", "text": "@{author} hi"},
        {"waves": ">=2", "type": "reply_to_peer", "peer": "op", "text": "x"}]}]
    spec = load_experiment(_experiment(tmp_path, peers))
    assert [p.type for p in spec.peers] == ["comment", "reply", "reply_to_agent_comments", "reply_to_peer"]


@pytest.mark.parametrize("peers,match", [
    ([{"account": "fish_a", "actions": []}], "role: operator"),
    ([{"account": "op", "actions": [{"type": "comment", "video": "nope", "text": "x"}]}], "not in the world"),
    ([{"account": "op", "actions": [{"type": "reply", "to_label": "missing", "text": "x"}]}], "unknown label"),
    ([{"account": "op", "actions": [{"type": "shout", "text": "x"}]}], "unknown"),
    ([{"account": "op", "actions": [{"type": "comment", "video": "cot", "text": " "}]}], "empty"),
])
def test_invalid_peers_rejected(tmp_path, peers, match):
    with pytest.raises(SpecError, match=match):
        load_experiment(_experiment(tmp_path, peers))
