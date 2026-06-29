"""PluginRegistry — Central plugin catalogue and service locator (C53)."""
from __future__ import annotations
import logging, threading
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PluginRegistry:
    """Catalogue of loaded plugins and their exported services."""

    def __init__(self, hook_dispatcher=None):
        self._dispatcher = hook_dispatcher
        self._plugins:  Dict[str, Any] = {}
        self._services: Dict[Tuple[str, str], Tuple[str, Any]] = {}
        self._lock = threading.Lock()

    def register_plugin(self, info) -> None:
        with self._lock:
            self._plugins[info.name] = info

    def unregister_plugin(self, name: str) -> bool:
        with self._lock:
            existed = name in self._plugins
            self._plugins.pop(name, None)
            stale = [k for k, (pname, _) in self._services.items() if pname == name]
            for k in stale: del self._services[k]
        return existed

    def get_plugin(self, name: str) -> Optional[Any]:
        return self._plugins.get(name)

    def all_plugins(self) -> List[Any]:
        with self._lock: return list(self._plugins.values())

    def register_service(
        self, plugin_name: str, service_type: str, name: str, obj: Any,
        *, overwrite: bool = False,
    ) -> bool:
        key = (service_type, name)
        with self._lock:
            if key in self._services and not overwrite:
                logger.warning(f"PluginRegistry: ({service_type}, '{name}') already registered")
                return False
            self._services[key] = (plugin_name, obj)
        return True

    def get_service(self, service_type: str, name: str) -> Optional[Any]:
        entry = self._services.get((service_type, name))
        return entry[1] if entry else None

    def list_services(self, service_type: str) -> List[Dict]:
        with self._lock:
            return [{"name": n, "plugin": pname, "object": obj}
                    for (stype, n), (pname, obj) in self._services.items()
                    if stype == service_type]

    def health(self) -> Dict:
        with self._lock:
            plugins  = list(self._plugins.values())
            services = list(self._services.keys())
        return {
            "plugins_loaded": len(plugins),
            "plugins": [{"name": p.name, "version": p.version,
                         "loaded": p.loaded, "error": p.error} for p in plugins],
            "services": len(services),
            "service_types": list({stype for stype, _ in services}),
        }
