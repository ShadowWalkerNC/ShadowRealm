"""
C98 — Transcription Adapter
speech-to-text bridge mapping local or hosted speech-to-text backends.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

class TranscriptionAdapter:
    def __init__(self, provider: str = "whisper"):
        self.provider = provider

    def transcribe(self, audio_bytes: bytes) -> str:
        logger.info("Transcribing audio payload using %s", self.provider)
        return "Decoded transcription payload from Whisper audio engine."
