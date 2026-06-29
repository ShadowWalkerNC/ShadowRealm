"""SessionManager — Server-side session lifecycle (C77).

Issues, stores, and invalidates server-side sessions.
Session tokens are cryptographically random; no user data is
stored in the token itself (unlike JWT).

Features:
  - Cryptographically random 32-byte session IDs
  - Configurable TTL with sliding expiry option
  - Per-session data store (arbitrary JSON-serialisable dict)
  - SQLite persistence or in-memory
  - Concurrent session limit per user
  - Fingerprint binding: tie session to IP / User-Agent
  - Bulk expiry sweep

Public API:
  sm = SessionManager(db_path=":memory:", ttl_s=3600)
  session_id = sm.create(user_id, *, data, fingerprint, ttl_s)
  session    = sm.get(session_id)           -> Session | None
  ok         = sm.touch(session_id)         # extend sliding TTL
  sm.set_data(session_id, key, value)
  sm.invalidate(session_id)
  sm.invalidate_all(user_id)
  sessions = sm.list_user(user_id)          -> list[Session]
  sm.sweep_expired()                        -> int  (count removed)
"""
from __future__ import annotations
import json, logging, os, sqlite3, threading, time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TTL         = 3_600.0
_MAX_SESSIONS_PER_USER = 10


@dataclass
class Session:
    session_id:  str
    user_id:     str
    data:        Dict[str, Any]
    created_at:  float
    expires_at:  float
    last_active: float
    fingerprint: str
    active:      bool


class SessionManager:
    """Server-side session store with sliding TTL and fingerprint binding."""

    def __init__(
        self,
        db_path:  str   = ":memory:",
        ttl_s:    float = _DEFAULT_TTL,
        sliding:  bool  = True,
        max_per_user: int = _MAX_SESSIONS_PER_USER,
    ):
        self._db      = sqlite3.connect(db_path, check_same_thread=False)
        self._ttl     = ttl_s
        self._sliding = sliding
        self._max     = max_per_user
        self._lock    = threading.Lock()
        self._init_db()

    def create(
        self,
        user_id: str,
        *,
        data:        Optional[Dict] = None,
        fingerprint: str  = "",
        ttl_s:       Optional[float] = None,
    ) -> str:
        self._enforce_limit(user_id)
        session_id  = os.urandom(32).hex()
        now         = time.time()
        expires_at  = now + (ttl_s or self._ttl)
        with self._lock:
            self._db.execute(
                "INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)",
                (session_id, user_id, json.dumps(data or {}),
                 now, expires_at, now, fingerprint, 1)
            )
            self._db.commit()
        return session_id

    def get(self, session_id: str, *, fingerprint: str = "") -> Optional[Session]:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM sessions WHERE session_id=? AND active=1", (session_id,)
            ).fetchone()
        if not row: return None
        sess = self._row(row)
        if time.time() > sess.expires_at:
            self.invalidate(session_id)
            return None
        if fingerprint and sess.fingerprint and sess.fingerprint != fingerprint:
            logger.warning(f"SessionManager: fingerprint mismatch for {session_id}")
            return None
        if self._sliding:
            self.touch(session_id)
        return sess

    def touch(self, session_id: str) -> bool:
        with self._lock:
            c = self._db.execute(
                "UPDATE sessions SET last_active=?, expires_at=? WHERE session_id=? AND active=1",
                (time.time(), time.time() + self._ttl, session_id)
            )
            self._db.commit()
        return c.rowcount > 0

    def set_data(self, session_id: str, key: str, value: Any) -> bool:
        with self._lock:
            row = self._db.execute(
                "SELECT data FROM sessions WHERE session_id=? AND active=1", (session_id,)
            ).fetchone()
            if not row: return False
            data = json.loads(row[0])
            data[key] = value
            self._db.execute(
                "UPDATE sessions SET data=? WHERE session_id=?",
                (json.dumps(data), session_id)
            )
            self._db.commit()
        return True

    def invalidate(self, session_id: str) -> bool:
        with self._lock:
            c = self._db.execute(
                "UPDATE sessions SET active=0 WHERE session_id=?", (session_id,)
            )
            self._db.commit()
        return c.rowcount > 0

    def invalidate_all(self, user_id: str) -> int:
        with self._lock:
            c = self._db.execute(
                "UPDATE sessions SET active=0 WHERE user_id=? AND active=1", (user_id,)
            )
            self._db.commit()
        return c.rowcount

    def list_user(self, user_id: str) -> List[Session]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM sessions WHERE user_id=? AND active=1", (user_id,)
            ).fetchall()
        return [self._row(r) for r in rows]

    def sweep_expired(self) -> int:
        with self._lock:
            c = self._db.execute(
                "UPDATE sessions SET active=0 WHERE expires_at<? AND active=1", (time.time(),)
            )
            self._db.commit()
        return c.rowcount

    def _enforce_limit(self, user_id: str) -> None:
        with self._lock:
            rows = self._db.execute(
                "SELECT session_id FROM sessions WHERE user_id=? AND active=1 ORDER BY created_at",
                (user_id,)
            ).fetchall()
        if len(rows) >= self._max:
            oldest = rows[0][0]
            self.invalidate(oldest)

    def _init_db(self) -> None:
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS sessions(
                session_id TEXT PRIMARY KEY, user_id TEXT,
                data TEXT, created_at REAL, expires_at REAL,
                last_active REAL, fingerprint TEXT, active INTEGER
            )
        """)
        self._db.execute("CREATE INDEX IF NOT EXISTS idx_sess_user ON sessions(user_id)")
        self._db.commit()

    @staticmethod
    def _row(row) -> Session:
        return Session(
            session_id=row[0], user_id=row[1],
            data=json.loads(row[2]), created_at=row[3],
            expires_at=row[4], last_active=row[5],
            fingerprint=row[6], active=bool(row[7]),
        )
