from __future__ import annotations

from fastapi import APIRouter

from app.integrations.plugins.plugin_registry import registry

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("")
def list_plugins():
    """List all loaded DeFi plugins."""
    plugins = registry.get_all()
    
    return {
        "status": "ok",
        "count": len(plugins),
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "supported_chains": p.supported_chains,
                "supported_events": p.supported_events,
            }
            for p in plugins
        ]
    }


@router.post("/reload")
def reload_plugins():
    """Reload all plugins from the directory."""
    registry.reload()
    return {"status": "ok", "message": f"Loaded {len(registry.get_all())} plugins."}
