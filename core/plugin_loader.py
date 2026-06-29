"""
C103 — Plugin Loader
Dynamic plugin discovery and loading from directories or entry points.
Supports hot-reload, dependency ordering, and lifecycle hooks.
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class PluginMeta:
    name: str
    version: str = "0.0.1"
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    author: str = ""


class PluginBase:
    """
    Base class all plugins must inherit from.
    Override setup() and teardown() for lifecycle management.
    """
    meta: PluginMeta = PluginMeta(name="unnamed")

    def setup(self, context: Any = None) -> None:
        """Called after the plugin is loaded."""

    def teardown(self) -> None:
        """Called before the plugin is unloaded."""


@dataclass
class LoadedPlugin:
    meta: PluginMeta
    instance: PluginBase
    module_path: str
    active: bool = True


class PluginError(Exception):
    pass


class PluginLoader:
    """
    Loads and manages plugins from filesystem paths or dotted module paths.

    Usage::

        loader = PluginLoader()
        loader.load_from_directory("plugins/")
        loader.setup_all(context=app_context)
    """

    def __init__(self):
        self._plugins: dict[str, LoadedPlugin] = {}
        self._hooks: dict[str, list[Callable]] = {}

    # ------------------------------------------------------------------ #
    #  Loading                                                             #
    # ------------------------------------------------------------------ #

    def load(self, module_path: str, context: Any = None) -> LoadedPlugin:
        """Load a plugin by dotted module path."""
        try:
            mod = importlib.import_module(module_path)
        except ImportError as e:
            raise PluginError(f"Cannot import plugin module '{module_path}': {e}") from e
        return self._register_module(mod, module_path, context)

    def load_file(self, path: str | Path, context: Any = None) -> LoadedPlugin:
        """Load a plugin from a .py file path."""
        p = Path(path)
        if not p.exists():
            raise PluginError(f"Plugin file not found: {path}")
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[p.stem] = mod
        spec.loader.exec_module(mod)
        return self._register_module(mod, str(p), context)

    def load_from_directory(
        self,
        directory: str | Path,
        pattern: str = "plugin_*.py",
        context: Any = None,
    ) -> list[LoadedPlugin]:
        """Auto-discover and load all matching plugin files in a directory."""
        d = Path(directory)
        if not d.is_dir():
            raise PluginError(f"Plugin directory not found: {directory}")
        loaded = []
        for filepath in sorted(d.glob(pattern)):
            try:
                lp = self.load_file(filepath, context)
                loaded.append(lp)
            except PluginError as e:
                logger.warning("Skipping plugin '%s': %s", filepath.name, e)
        return self._resolve_load_order(loaded)

    def _register_module(self, mod, module_path: str, context: Any) -> LoadedPlugin:
        plugin_cls = self._find_plugin_class(mod)
        if plugin_cls is None:
            raise PluginError(f"No PluginBase subclass found in '{module_path}'")
        instance = plugin_cls()
        meta = getattr(instance, "meta", PluginMeta(name=getattr(mod, "__name__", module_path)))
        if meta.name in self._plugins:
            logger.warning("Plugin '%s' already loaded; replacing.", meta.name)
        lp = LoadedPlugin(meta=meta, instance=instance, module_path=module_path)
        self._plugins[meta.name] = lp
        instance.setup(context)
        self._fire("plugin.loaded", lp)
        logger.info("Loaded plugin '%s' v%s", meta.name, meta.version)
        return lp

    def _find_plugin_class(self, mod) -> Optional[Type[PluginBase]]:
        for attr in dir(mod):
            obj = getattr(mod, attr)
            try:
                if (
                    isinstance(obj, type)
                    and issubclass(obj, PluginBase)
                    and obj is not PluginBase
                ):
                    return obj
            except TypeError:
                pass
        return None

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def setup_all(self, context: Any = None) -> None:
        for lp in self._plugins.values():
            lp.instance.setup(context)

    def unload(self, name: str) -> None:
        lp = self._get(name)
        lp.instance.teardown()
        lp.active = False
        self._fire("plugin.unloaded", lp)
        del self._plugins[name]
        logger.info("Unloaded plugin '%s'", name)

    def reload(self, name: str, context: Any = None) -> LoadedPlugin:
        lp = self._get(name)
        path = lp.module_path
        self.unload(name)
        return self.load_file(path, context)

    # ------------------------------------------------------------------ #
    #  Hooks                                                               #
    # ------------------------------------------------------------------ #

    def on(self, event: str, fn: Callable) -> None:
        self._hooks.setdefault(event, []).append(fn)

    def _fire(self, event: str, data: Any) -> None:
        for fn in self._hooks.get(event, []):
            try:
                fn(data)
            except Exception as e:
                logger.warning("Plugin hook error [%s]: %s", event, e)

    # ------------------------------------------------------------------ #
    #  Introspection                                                       #
    # ------------------------------------------------------------------ #

    def get(self, name: str) -> PluginBase:
        return self._get(name).instance

    def list_plugins(self) -> list[PluginMeta]:
        return [lp.meta for lp in self._plugins.values()]

    def is_loaded(self, name: str) -> bool:
        return name in self._plugins

    def _get(self, name: str) -> LoadedPlugin:
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' not loaded")
        return self._plugins[name]

    def _resolve_load_order(self, plugins: list[LoadedPlugin]) -> list[LoadedPlugin]:
        """Topological sort by declared dependencies."""
        name_map = {lp.meta.name: lp for lp in plugins}
        visited: set[str] = set()
        order: list[LoadedPlugin] = []

        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            lp = name_map.get(name)
            if lp:
                for dep in lp.meta.dependencies:
                    visit(dep)
                order.append(lp)

        for lp in plugins:
            visit(lp.meta.name)
        return order

    def __len__(self) -> int:
        return len(self._plugins)
