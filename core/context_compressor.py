"""
C113 — Context Compressor
Condenses prompts when nearing target model context limit rules.
"""
from __future__ import annotations

class ContextCompressor:
    @staticmethod
    def compress_messages(messages: list[dict], threshold: int = 100) -> list[dict]:
        # Compact or drop older messages if they exceed the threshold limit
        if len(messages) > threshold:
            return [{"role": "system", "content": "Compressed context overview"}] + messages[-threshold:]
        return messages
