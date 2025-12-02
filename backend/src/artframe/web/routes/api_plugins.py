"""
Plugin and instance management API routes for Artframe dashboard.

Includes plugin listing, details, and instance CRUD operations.
"""

from fastapi import APIRouter, HTTPException

from ..schemas import (
    APIResponse,
    InstanceCreateRequest,
    InstanceResponse,
    InstancesListResponse,
    InstanceUpdateRequest,
    PluginResponse,
    PluginsListResponse,
)
from . import get_state

router = APIRouter()


# ===== Plugin Management APIs =====


@router.get("/api/plugins", response_model=PluginsListResponse)
def api_plugins_list():
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
        raise HTTPException(status_code=500, detail=str(e))


# ===== Plugin Instance Management APIs =====
# NOTE: These routes must come BEFORE /api/plugins/{plugin_id} to avoid route conflicts


@router.get("/api/plugins/instances", response_model=InstancesListResponse)
def api_instances_list():
    """Get list of all plugin instances."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        instances = instance_manager.list_instances()

        instances_data = []
        for inst in instances:
            instances_data.append(
                {
                    "id": inst.id,
                    "plugin_id": inst.plugin_id,
                    "name": inst.name,
                    "settings": inst.settings,
                    "enabled": inst.enabled,
                    "created_at": inst.created_at.isoformat(),
                    "updated_at": inst.updated_at.isoformat(),
                }
            )

        return {"success": True, "data": instances_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/instances", response_model=InstanceResponse)
def api_instances_create(request: InstanceCreateRequest):
    """Create a new plugin instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        instance = instance_manager.create_instance(
            request.plugin_id, request.name, request.settings
        )

        if instance is None:
            raise HTTPException(
                status_code=400, detail="Failed to create instance (check validation)"
            )

        return {
            "success": True,
            "data": {
                "id": instance.id,
                "plugin_id": instance.plugin_id,
                "name": instance.name,
                "settings": instance.settings,
                "enabled": instance.enabled,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/instances/{instance_id}", response_model=InstanceResponse)
def api_instance_details(instance_id: str):
    """Get details for a specific instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        instance = instance_manager.get_instance(instance_id)

        if instance is None:
            raise HTTPException(status_code=404, detail="Instance not found")

        return {
            "success": True,
            "data": {
                "id": instance.id,
                "plugin_id": instance.plugin_id,
                "name": instance.name,
                "settings": instance.settings,
                "enabled": instance.enabled,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/plugins/instances/{instance_id}", response_model=InstanceResponse)
def api_instance_update(instance_id: str, request: InstanceUpdateRequest):
    """Update an instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        success = instance_manager.update_instance(instance_id, request.name, request.settings)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update instance")

        instance = instance_manager.get_instance(instance_id)
        if instance is None:
            raise HTTPException(status_code=404, detail="Instance not found")

        return {
            "success": True,
            "data": {
                "id": instance.id,
                "plugin_id": instance.plugin_id,
                "name": instance.name,
                "settings": instance.settings,
                "enabled": instance.enabled,
                "created_at": instance.created_at.isoformat(),
                "updated_at": instance.updated_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/plugins/instances/{instance_id}", response_model=APIResponse)
def api_instance_delete(instance_id: str):
    """Delete an instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        success = instance_manager.delete_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete instance")

        return {"success": True, "message": "Instance deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/instances/{instance_id}/enable", response_model=APIResponse)
def api_instance_enable(instance_id: str):
    """Enable an instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        success = instance_manager.enable_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to enable instance")

        return {"success": True, "message": "Instance enabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/instances/{instance_id}/disable", response_model=APIResponse)
def api_instance_disable(instance_id: str):
    """Disable an instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager
        success = instance_manager.disable_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to disable instance")

        return {"success": True, "message": "Instance disabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/instances/{instance_id}/test", response_model=APIResponse)
def api_instance_test(instance_id: str):
    """Test run a plugin instance."""
    state = get_state()

    try:
        instance_manager = state.instance_manager

        # Get device config from display controller
        device_config = {
            "width": 600,  # TODO: Get from actual display
            "height": 448,
            "rotation": 0,
            "color_mode": "grayscale",
        }

        success, error_msg = instance_manager.test_instance(instance_id, device_config)

        if not success:
            raise HTTPException(status_code=400, detail=error_msg or "Test failed")

        return {"success": True, "message": "Instance test successful"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Plugin Details API =====
# NOTE: This route must come AFTER /api/plugins/instances* routes to avoid conflicts


@router.get("/api/plugins/{plugin_id}", response_model=PluginResponse)
def api_plugin_details(plugin_id: str):
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
        raise HTTPException(status_code=500, detail=str(e))
