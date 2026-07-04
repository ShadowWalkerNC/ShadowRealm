"""
C115 — Command Parser
Parses system commands (/q, /background, /reset, /compress) from prompt streams.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional

class CommandParser:
    @staticmethod
    def parse_command(text: str) -> Tuple[Optional[str], Optional[str]]:
        if text.startswith("/"):
            parts = text.split(" ", 1)
            cmd = parts[0][1:]
            arg = parts[1] if len(parts) > 1 else None
            return cmd, arg
        return None, None
