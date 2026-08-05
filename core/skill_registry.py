"""SkillRegistry — loads skills/*.md, progressive disclosure (name+desc only in context)."""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SkillRegistry:
    """Registry managing skills with Progressive Disclosure.

    Contract:
      - Startup: Load only name + description into memory (~53 tokens per skill).
      - On-Demand: Load full instructions, triggers, examples, and failure modes when active.
    """

    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = Path(__file__).parent.parent / "skills"
        
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._index: Dict[str, Dict[str, Any]] = {}
        self.reload_index()

    def reload_index(self) -> int:
        """Scan skills directory and build lightweight index (name + description)."""
        self._index.clear()
        if not self.skills_dir.exists():
            return 0

        for file_path in self.skills_dir.glob("*.md"):
            try:
                metadata = self._extract_metadata(file_path)
                if metadata and "name" in metadata:
                    self._index[metadata["name"]] = {
                        "name": metadata["name"],
                        "description": metadata.get("description", ""),
                        "path": str(file_path.resolve()),
                    }
            except Exception as e:
                logger.error(f"Error indexing skill {file_path}: {e}")

        return len(self._index)

    def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract title/name and description from frontmatter or top headers."""
        content = file_path.read_text(encoding="utf-8")
        
        # Check for YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    data = yaml.safe_load(parts[1])
                    if isinstance(data, dict):
                        return data
                except Exception:
                    pass

        # Markdown header fallback parse
        name = file_path.stem
        description = ""
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("# "):
                name = line.replace("# ", "").strip()
            elif line.startswith("## Description"):
                if i + 1 < len(lines):
                    description = lines[i + 1].strip()

        return {"name": name, "description": description}

    def get_progressive_context(self) -> List[Dict[str, str]]:
        """Return lightweight index for system prompt injection (Progressive Disclosure)."""
        return [
            {"name": item["name"], "description": item["description"]}
            for item in self._index.values()
        ]

    def get_full_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Load full instructions, examples, and failure modes on demand."""
        if skill_name not in self._index:
            return None

        file_path = Path(self._index[skill_name]["path"])
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return {
            "name": skill_name,
            "path": str(file_path),
            "content": content,
            "metadata": self._index[skill_name],
        }

    def list_skills(self) -> List[str]:
        """List registered skill names."""
        return list(self._index.keys())
