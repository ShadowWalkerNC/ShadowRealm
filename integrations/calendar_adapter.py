"""
C107 — Calendar Adapter
Connects to CalDAV / local calendar services to read/write event payloads.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CalendarAdapter:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._events: List[Dict[str, Any]] = []

    def add_event(self, summary: str, dt_start: str, dt_end: str) -> Dict[str, Any]:
        event = {
            "summary": summary,
            "dt_start": dt_start,
            "dt_end": dt_end,
            "id": f"event-{len(self._events)}"
        }
        self._events.append(event)
        logger.info("Added event: %s", summary)
        return event

    def list_events(self) -> List[Dict[str, Any]]:
        return self._events
