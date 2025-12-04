"""
Plugin and instance management API routes for Artframe dashboard.

Provides endpoints for plugin listing and instance CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_device_config, get_instance_manager
from ..schemas import (
    APIResponse,
    InstanceCreateRequest,
    InstanceResponse,
    InstancesListResponse,
    InstanceUpdateRequest,
    PluginResponse,
    PluginsListResponse,
)

router = APIRouter(prefix="/api/plugins", tags=["Plugins"])


# ===== Plugin List =====


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


# ===== Instance Management =====
# NOTE: These routes MUST come BEFORE /{plugin_id} to avoid route conflicts
# Otherwise "instances" gets matched as a plugin_id


@router.get("/instances", response_model=InstancesListResponse)
def list_instances(instance_manager=Depends(get_instance_manager)):
    """Get list of all plugin instances."""
    try:
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
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/instances", response_model=InstanceResponse)
def create_instance(request: InstanceCreateRequest, instance_manager=Depends(get_instance_manager)):
    """Create a new plugin instance."""
    try:
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
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/instances/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: str, instance_manager=Depends(get_instance_manager)):
    """Get details for a specific instance."""
    try:
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
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/instances/{instance_id}", response_model=InstanceResponse)
def update_instance(
    instance_id: str,
    request: InstanceUpdateRequest,
    instance_manager=Depends(get_instance_manager),
):
    """Update an instance."""
    try:
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
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/instances/{instance_id}", response_model=APIResponse)
def delete_instance(instance_id: str, instance_manager=Depends(get_instance_manager)):
    """Delete an instance."""
    try:
        success = instance_manager.delete_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete instance")

        return {"success": True, "message": "Instance deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/instances/{instance_id}/enable", response_model=APIResponse)
def enable_instance(instance_id: str, instance_manager=Depends(get_instance_manager)):
    """Enable an instance."""
    try:
        success = instance_manager.enable_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to enable instance")

        return {"success": True, "message": "Instance enabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/instances/{instance_id}/disable", response_model=APIResponse)
def disable_instance(instance_id: str, instance_manager=Depends(get_instance_manager)):
    """Disable an instance."""
    try:
        success = instance_manager.disable_instance(instance_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to disable instance")

        return {"success": True, "message": "Instance disabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/instances/{instance_id}/test", response_model=APIResponse)
def test_instance(
    instance_id: str,
    instance_manager=Depends(get_instance_manager),
    device_config=Depends(get_device_config),
):
    """Test run a plugin instance."""
    try:
        success, error_msg = instance_manager.test_instance(instance_id, device_config)

        if not success:
            raise HTTPException(status_code=400, detail=error_msg or "Test failed")

        return {"success": True, "message": "Instance test successful"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ===== Plugin Details =====
# NOTE: This route MUST come AFTER /instances routes to avoid conflicts


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
