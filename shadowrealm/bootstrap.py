"""Register ShadowRealm routes on the Odysseus FastAPI app.

Called from ``app.py`` via a one-line ``# SHADOWREALM:`` hook so upstream
Odysseus updates to ``app.py`` only conflict on that single line.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register(app) -> None:
    """Include ShadowRealm routers. Safe to call once at startup."""
    from shadowrealm.routing_routes import setup_routing_routes

    app.include_router(setup_routing_routes())
    logger.info("ShadowRealm extensions registered (routing + workflows)")
