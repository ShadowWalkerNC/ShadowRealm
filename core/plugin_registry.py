"""PluginRegistry — Versioned plugin manifest + dependency resolver (C85).

Tracks installed plugins with versioned manifests, resolves load order
via dependency graph, and enforces compatibility constraints.

Plugin manifest keys:
  name        str   unique plugin identifier
  version     str   semver string e.g. "1.2.3"
  entry       str   dotted import path to plugin class/function
  depends_on  list  ["other_plugin>=1.0.0", ...]
  api_version str   min ShadowRealm core API version required
  description str
  enabled     bool

Features:
  - Register / unregister plugins with manifest validation
  - Semver-aware dependency resolution (no external deps)
  - Circular dependency detection
  - Topological load order via Kahn's algorithm
  - Enable / disable without unregistering
  - List plugins filtered by state
  - SQLite persistence or in-memory

Public API:
  pr = PluginRegistry(db_path=":memory:")
  pr.register(manifest: dict) -> str          # returns plugin name
  pr.unregister(name)
  pr.enable(name) / pr.disable(name)
  pr.resolve_load_order() -> list[str]
  pr.get(name) -> dict | None
  pr.list(enabled_only=False) -> list[dict]
"""
from __future__ import annotations
import json, logging, re, sqlite3, threading
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_SEMVER_RE = re.compile(r'^(\d+)\.(\d+)\.(\d+)')
_DEP_RE    = re.compile(r'^([\w\-]+)(?:>=(\d+\.\d+\.\d+))?$')


def _parse_version(v: str) -> Tuple[int, int, int]:
    m = _SEMVER_RE.match(v or "0.0.0")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)


class PluginRegistry:
    """Versioned plugin manifest store with dependency-aware load ordering."""

    _DDL = """
        CREATE TABLE IF NOT EXISTS plugins (
            name        TEXT PRIMARY KEY,
            version     TEXT NOT NULL,
            entry       TEXT NOT NULL,
            depends_on  TEXT NOT NULL DEFAULT '[]',
            api_version TEXT NOT NULL DEFAULT '0.0.0',
            description TEXT NOT NULL DEFAULT '',
            enabled     INTEGER NOT NULL DEFAULT 1
        );
    """

    _REQUIRED = {"name", "version", "entry"}

    def __init__(self, db_path: str = ":memory:"):
        self._db   = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._db.execute(self._DDL)
            self._db.commit()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, manifest: Dict) -> str:
        missing = self._REQUIRED - manifest.keys()
        if missing:
            raise ValueError(f"PluginRegistry: missing manifest keys: {missing}")
        name = manifest["name"]
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO plugins VALUES(?,?,?,?,?,?,?)",
                (
                    name,
                    manifest["version"],
                    manifest["entry"],
                    json.dumps(manifest.get("depends_on", [])),
                    manifest.get("api_version", "0.0.0"),
                    manifest.get("description", ""),
                    int(manifest.get("enabled", True)),
                )
            )
            self._db.commit()
        logger.info(f"PluginRegistry: registered '{name}' v{manifest['version']}")
        return name

    def unregister(self, name: str) -> bool:
        with self._lock:
            c = self._db.execute("DELETE FROM plugins WHERE name=?", (name,))
            self._db.commit()
        return c.rowcount > 0

    def enable(self, name: str) -> None:
        self._set_enabled(name, True)

    def disable(self, name: str) -> None:
        self._set_enabled(name, False)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[Dict]:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM plugins WHERE name=?", (name,)
            ).fetchone()
        return self._hydrate(row) if row else None

    def list(self, *, enabled_only: bool = False) -> List[Dict]:
        q = "SELECT * FROM plugins"
        if enabled_only:
            q += " WHERE enabled=1"
        with self._lock:
            rows = self._db.execute(q).fetchall()
        return [self._hydrate(r) for r in rows]

    # ------------------------------------------------------------------
    # Dependency resolution
    # ------------------------------------------------------------------

    def resolve_load_order(self) -> List[str]:
        """Return topologically sorted plugin names (Kahn's algorithm)."""
        plugins  = {p["name"]: p for p in self.list(enabled_only=True)}
        in_degree: Dict[str, int] = {n: 0 for n in plugins}
        graph:     Dict[str, List[str]] = {n: [] for n in plugins}

        for name, plugin in plugins.items():
            for dep_str in plugin["depends_on"]:
                m = _DEP_RE.match(dep_str.strip())
                if not m:
                    continue
                dep_name, dep_min = m.group(1), m.group(2)
                if dep_name not in plugins:
                    raise RuntimeError(
                        f"PluginRegistry: '{name}' requires '{dep_name}' which is not registered"
                    )
                if dep_min:
                    installed = _parse_version(plugins[dep_name]["version"])
                    required  = _parse_version(dep_min)
                    if installed < required:
                        raise RuntimeError(
                            f"PluginRegistry: '{name}' needs '{dep_name}>={dep_min}' "
                            f"but {plugins[dep_name]['version']} is installed"
                        )
                graph[dep_name].append(name)
                in_degree[name] += 1

        queue  = [n for n, d in in_degree.items() if d == 0]
        order: List[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for successor in graph[node]:
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        if len(order) != len(plugins):
            cycle = set(plugins) - set(order)
            raise RuntimeError(f"PluginRegistry: circular dependency detected: {cycle}")
        return order

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_enabled(self, name: str, state: bool) -> None:
        with self._lock:
            self._db.execute(
                "UPDATE plugins SET enabled=? WHERE name=?",
                (int(state), name)
            )
            self._db.commit()

    @staticmethod
    def _hydrate(row: tuple) -> Dict:
        return {
            "name":        row[0], "version":     row[1],
            "entry":       row[2],
            "depends_on":  json.loads(row[3]),
            "api_version": row[4], "description": row[5],
            "enabled":     bool(row[6]),
        }
