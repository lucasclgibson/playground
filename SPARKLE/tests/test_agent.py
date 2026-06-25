import pytest

from sparkle import agent as agent_mod
from sparkle import tools


def test_create_default_and_reload(tmp_path):
    d = tmp_path / "gizmo"
    a = agent_mod.create_default(d, "gizmo")
    assert (d / "system.md").exists()
    assert (d / "soul.md").exists()
    assert (d / "tools.md").exists()
    assert "gizmo" in a.system
    assert "update_self" in a.tools

    reloaded = agent_mod.load(d, "gizmo")
    assert reloaded.soul == a.soul
    prompt = reloaded.build_system_prompt()
    assert "# System" in prompt and "# Soul" in prompt and "# Tools" in prompt


def test_update_self_writes_only_provided_fields(tmp_path):
    d = tmp_path / "gizmo"
    agent_mod.create_default(d, "gizmo")
    old_system = (d / "system.md").read_text()

    note = tools.execute(d, {"soul": "a serene haiku-speaking monk"})
    assert "soul.md" in note
    assert "/reset" in note
    assert "monk" in (d / "soul.md").read_text()
    # untouched files stay as they were
    assert (d / "system.md").read_text() == old_system
    # a backup of the previous soul was kept
    assert (d / "soul.md.bak").exists()


def test_update_self_refuses_empty(tmp_path):
    d = tmp_path / "gizmo"
    agent_mod.create_default(d, "gizmo")
    before = (d / "soul.md").read_text()
    note = tools.execute(d, {"soul": "   "})
    assert (d / "soul.md").read_text() == before
    assert "empty" in note.lower() or "nothing changed" in note.lower()


def test_update_self_no_fields(tmp_path):
    d = tmp_path / "gizmo"
    agent_mod.create_default(d, "gizmo")
    note = tools.execute(d, {})
    assert "nothing changed" in note.lower()


def test_atomic_write_refuses_empty(tmp_path):
    with pytest.raises(ValueError):
        agent_mod._atomic_write(tmp_path / "x.md", "   ")
