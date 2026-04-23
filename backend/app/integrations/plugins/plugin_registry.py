"""
DeFi Plugin Registry.

Dynamically loads all plugins in the `plugins/` directory and manages
their integration into the core DeFi recognition engine.
"""
from __future__ import annotations

import importlib
import inspect
import os
import sys
from pathlib import Path

from app.integrations.plugins.plugin_base import DeFiPlugin


class PluginRegistry:
    """Singleton registry for DeFi plugins."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginRegistry, cls).__new__(cls)
            cls._instance.plugins: dict[str, DeFiPlugin] = {}
            cls._instance.merged_addresses: dict[str, dict[str, str]] = {}
            cls._instance.initialized = False
        return cls._instance

    def initialize(self):
        """Auto-discover and load all plugins."""
        if self.initialized:
            return

        self.plugins.clear()
        self.merged_addresses.clear()
        
        plugins_dir = Path(__file__).parent
        if not plugins_dir.exists():
            return

        # Add app dir to path to allow absolute imports
        app_dir = plugins_dir.parents[2]
        if str(app_dir) not in sys.path:
            sys.path.insert(0, str(app_dir))

        for file_path in plugins_dir.glob("*_plugin.py"):
            module_name = f"app.integrations.plugins.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                # Find classes that inherit from DeFiPlugin but aren't the base class itself
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, DeFiPlugin) and obj is not DeFiPlugin:
                        plugin_instance = obj()
                        self.register(plugin_instance)
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")

        self.initialized = True

    def register(self, plugin: DeFiPlugin):
        """Register a specific plugin instance."""
        self.plugins[plugin.name] = plugin
        
        # Merge addresses
        for chain, addrs in plugin.get_known_addresses().items():
            if chain not in self.merged_addresses:
                self.merged_addresses[chain] = {}
            
            # plugin addresses override core addresses in case of conflict
            for addr, label in addrs.items():
                self.merged_addresses[chain][addr.lower()] = f"{plugin.name.upper()}: {label}"

    def get_all(self) -> list[DeFiPlugin]:
        """Get all loaded plugins."""
        if not self.initialized:
            self.initialize()
        return list(self.plugins.values())

    def get_by_protocol(self, name: str) -> DeFiPlugin | None:
        """Get a specific plugin by protocol name."""
        if not self.initialized:
            self.initialize()
        return self.plugins.get(name)

    def get_merged_addresses(self) -> dict[str, dict[str, str]]:
        """Get the globally merged address dictionary from all plugins."""
        if not self.initialized:
            self.initialize()
        return self.merged_addresses

    def reload(self):
        """Force reload of all plugins (for hot-reloading)."""
        self.initialized = False
        self.initialize()


# Global accessor
registry = PluginRegistry()
