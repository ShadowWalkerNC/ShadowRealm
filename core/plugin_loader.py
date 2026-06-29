"""PluginLoader — Dynamic plugin discovery and import (C52)."""
from __future__ import annotations
import importlib, importlib.util, logging, sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    requires: List[str]
    hooks: List[str]
    module: Any
    path: str
    loaded: bool = True
    error: Optional[str] = None

class PluginLoader:
    """Discovers, imports, and manages plugin lifecycle."""

    def __init__(self, registry, plugin_dir: str = "plugins"):
        self._registry = registry
        self._plugin_dir = plugin_dir
        self._plugins: Dict[str, PluginInfo] = {}

    def load_dir(self, path: Optional[str] = None) -> List[PluginInfo]:
        scan_path = Path(path or self._plugin_dir)
        if not scan_path.exists():
            return []
        loaded = []
        for entry in sorted(scan_path.iterdir()):
            if entry.suffix == ".py" and not entry.name.startswith("_"):
                info = self._import_file(str(entry), entry.stem)
                if info: loaded.append(info)
            elif entry.is_dir() and (entry / "__init__.py").exists():
                info = self._import_file(str(entry / "__init__.py"), entry.name)
                if info: loaded.append(info)
        return loaded

    def load_module(self, dotted_path: str) -> Optional[PluginInfo]:
        try:
            mod = importlib.import_module(dotted_path)
            return self._register_module(mod, dotted_path)
        except Exception as e:
            logger.error(f"PluginLoader: failed to import '{dotted_path}': {e}")
            return None

    def reload(self, name: str) -> Optional[PluginInfo]:
        info = self._plugins.get(name)
        if not info: return None
        try:
            importlib.reload(info.module)
            return self._register_module(info.module, info.path, force=True)
        except Exception as e:
            logger.error(f"PluginLoader: reload '{name}' failed: {e}")
            return None

    def unload(self, name: str) -> bool:
        info = self._plugins.pop(name, None)
        if not info: return False
        cleanup = getattr(info.module, "teardown", None)
        if callable(cleanup):
            try: cleanup(self._registry)
            except Exception as e: logger.warning(f"PluginLoader: teardown '{name}': {e}")
        return True

    def loaded(self) -> List[PluginInfo]:
        return [p for p in self._plugins.values() if p.loaded]

    def _import_file(self, filepath: str, module_name: str) -> Optional[PluginInfo]:
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            mod  = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            return self._register_module(mod, filepath)
        except Exception as e:
            logger.error(f"PluginLoader: error loading '{filepath}': {e}")
            pi = PluginInfo(name=module_name, version="", description="",
                            author="", requires=[], hooks=[], module=None,
                            path=filepath, loaded=False, error=str(e))
            self._plugins[module_name] = pi
            return pi

    def _register_module(self, mod, path: str, force: bool = False) -> Optional[PluginInfo]:
        meta = getattr(mod, "PLUGIN_META", {})
        name = meta.get("name") or getattr(mod, "__name__", path)
        if name in self._plugins and not force:
            return self._plugins[name]
        for req in meta.get("requires", []):
            if req not in self._plugins:
                logger.warning(f"PluginLoader: '{name}' requires '{req}' not loaded")
        info = PluginInfo(
            name=name, version=meta.get("version", "0.0.0"),
            description=meta.get("description", ""), author=meta.get("author", ""),
            requires=meta.get("requires", []), hooks=meta.get("hooks", []),
            module=mod, path=path,
        )
        self._plugins[name] = info
        setup = getattr(mod, "setup", None)
        if callable(setup):
            try: setup(self._registry)
            except Exception as e:
                logger.error(f"PluginLoader: setup() '{name}': {e}")
                info.error = str(e)
        logger.info(f"PluginLoader: loaded '{name}' v{info.version}")
        return info
