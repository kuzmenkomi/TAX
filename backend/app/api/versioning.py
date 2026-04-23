from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute


def register_v1_aliases(api: FastAPI) -> None:
    existing_routes = [route for route in api.routes if isinstance(route, APIRoute)]
    existing_paths = {route.path for route in existing_routes}

    for route in existing_routes:
        path = route.path
        
        # If it already has /api/v1, create a legacy alias /v1/...
        if path.startswith("/api/v1"):
            legacy_path = path.replace("/api/v1", "/v1", 1)
            if legacy_path not in existing_paths:
                api.add_api_route(
                    legacy_path,
                    route.endpoint,
                    methods=list(route.methods or []),
                    response_model=None,
                    include_in_schema=False,
                    name=f"legacy_v1_{route.name}",
                )
                existing_paths.add(legacy_path)
            continue
            
        # DANGER: If it contains 'v1' anywhere, do NOT prepend /v1
        if "/v1" in path:
            continue

        # If it starts with /api, skip (it should already be versioned or be a special endpoint)
        if path.startswith("/api"):
            continue

        versioned_path = f"/v1{path}"
        if versioned_path not in existing_paths:
            api.add_api_route(
                versioned_path,
                route.endpoint,
                methods=list(route.methods or []),
                response_model=None,
                include_in_schema=False,
                name=f"v1_{route.name}",
            )
            existing_paths.add(versioned_path)
