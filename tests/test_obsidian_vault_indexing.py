import os
import json
import pytest
from src import constants

def _write_memories(tmp_path, memories):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "memory.json").write_text(json.dumps(memories), encoding="utf-8")
    return data_dir

@pytest.mark.asyncio
async def test_action_index_obsidian_vault(monkeypatch, tmp_path):
    from src.builtin_actions import action_index_obsidian_vault
    
    # Set up memory.json mock path
    data_dir = _write_memories(tmp_path, [])
    monkeypatch.setattr(constants, "DATA_DIR", str(data_dir))
    
    # Create a mock Obsidian vault folder with some markdown notes
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    (vault_dir / "Note1.md").write_text("Hello from note 1. This is project content.", encoding="utf-8")
    (vault_dir / "Note2.md").write_text("Note 2 information.", encoding="utf-8")
    
    msg, ok = await action_index_obsidian_vault("alice", vault_path=str(vault_dir))
    assert ok is True
    assert "Added 2 new memory entries" in msg
    
    # Verify entries were saved
    memory_file = data_dir / "memory.json"
    with open(memory_file, "r", encoding="utf-8") as f:
        memories = json.load(f)
        
    assert len(memories) == 2
    assert memories[0]["owner"] == "alice"
    assert memories[0]["tier"] == "cool"
    assert "Obsidian note [Note1]" in memories[0]["text"]
