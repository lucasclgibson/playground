import importlib

import pytest


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from sparkle import config
    importlib.reload(config)
    return config


def test_provider_round_trip(cfg):
    cfg.save_provider("ollama", "http://localhost:11434/v1", "", "llama3.2")
    p = cfg.get_provider()
    assert p == {
        "kind": "ollama",
        "base_url": "http://localhost:11434/v1",
        "api_key": "",
        "model": "llama3.2",
    }


def test_agent_registry_and_resolution(cfg, tmp_path):
    cfg.register_agent("gizmo", str(tmp_path / "gizmo"))
    cfg.register_agent("sage", str(tmp_path / "sage"))

    # last registered becomes default
    assert cfg.resolve_agent(None)["name"] == "sage"
    # explicit lookup
    assert cfg.resolve_agent("gizmo")["name"] == "gizmo"
    # unknown name
    assert cfg.resolve_agent("nope") is None

    cfg.set_last("gizmo")
    assert cfg.resolve_agent(None)["name"] == "gizmo"


def test_resolve_with_no_agents(cfg):
    assert cfg.resolve_agent(None) is None
    assert cfg.resolve_agent("anything") is None


def test_escaping_survives_round_trip(cfg, tmp_path):
    weird = str(tmp_path / 'a"b\\c')
    cfg.register_agent("weird", weird)
    assert cfg.resolve_agent("weird")["path"] == weird
