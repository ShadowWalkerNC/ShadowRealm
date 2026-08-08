"""ShadowRealm fork extensions on top of Odysseus.

These modules are intentionally kept out of Odysseus ``core/`` / ``routes/``
so upstream Odysseus syncs stay clean. Prefer adding here; touch Odysseus
files only via thin ``# SHADOWREALM:`` hooks.
"""

__all__ = ["bootstrap"]
