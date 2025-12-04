"""
Plugin API routes for Artframe dashboard.

Provides endpoints for plugin listing and details at /api/plugins/*.
Instance management has been moved to instances.py at /api/instances/*.
"""

from fastapi import APIRouter, HTTPException

from ..schemas import PluginResponse, PluginsListResponse

router = APIRouter(prefix="/api/plugins", tags=["Plugins"])


@router.get("", response_model=PluginsListResponse)
def list_plugins():
    """Get list of all available plugins."""
    try:
        from ...plugins.plugin_registry import list_plugin_metadata

        plugins_data = []
        for metadata in list_plugin_metadata():
            plugins_data.append(
                {
                    "id": metadata.plugin_id,
                    "display_name": metadata.display_name,
                    "class_name": metadata.class_name,
                    "description": metadata.description,
                    "author": metadata.author,
                    "version": metadata.version,
                    "icon": metadata.icon,
                    "settings_schema": metadata.settings_schema,
                }
            )

        return {"success": True, "data": plugins_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: str):
    """Get details for a specific plugin."""
    try:
        from ...plugins.plugin_registry import get_plugin_metadata

        metadata = get_plugin_metadata(plugin_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")

        return {
            "success": True,
            "data": {
                "id": metadata.plugin_id,
                "display_name": metadata.display_name,
                "class_name": metadata.class_name,
                "description": metadata.description,
                "author": metadata.author,
                "version": metadata.version,
                "icon": metadata.icon,
                "settings_schema": metadata.settings_schema,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
