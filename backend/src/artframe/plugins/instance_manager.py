"""
Instance manager for plugin instances.

Manages creation, storage, and lifecycle of plugin instances.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from ..models import PluginInstance
from ..utils import ensure_dir, load_json, now_in_tz, save_json
from .plugin_registry import get_plugin

logger = logging.getLogger(__name__)


class InstanceManager:
    """
    Manages plugin instances.

    Provides CRUD operations for plugin instances with persistence
    to JSON storage.
    """

    def __init__(self, storage_dir: Path, timezone: str = "UTC"):
        """
        Initialize instance manager.

        Args:
            storage_dir: Directory for storing instance data
            timezone: Timezone for timestamps (e.g., "Australia/Sydney")
        """
        self.storage_dir = ensure_dir(Path(storage_dir))
        self.timezone = ZoneInfo(timezone)
        self._now = lambda: now_in_tz(self.timezone)

        self.instances_file = self.storage_dir / "plugin_instances.json"
        self._instances: dict[str, PluginInstance] = {}

        # Load existing instances
        self._load_instances()

    def _load_instances(self) -> None:
        """Load instances from storage."""
        data = load_json(self.instances_file)
        if data is None:
            logger.info("No existing instances found")
            return

        for instance_data in data.get("instances", []):
            instance = PluginInstance(
                id=instance_data["id"],
                plugin_id=instance_data["plugin_id"],
                name=instance_data["name"],
                settings=instance_data["settings"],
                enabled=instance_data["enabled"],
                created_at=datetime.fromisoformat(instance_data["created_at"]),
                updated_at=datetime.fromisoformat(instance_data["updated_at"]),
            )
            self._instances[instance.id] = instance

        logger.info(f"Loaded {len(self._instances)} plugin instances")

    def _save_instances(self) -> None:
        """Save instances to storage."""
        data = {
            "instances": [
                {
                    "id": inst.id,
                    "plugin_id": inst.plugin_id,
                    "name": inst.name,
                    "settings": inst.settings,
                    "enabled": inst.enabled,
                    "created_at": inst.created_at.isoformat(),
                    "updated_at": inst.updated_at.isoformat(),
                }
                for inst in self._instances.values()
            ],
            "last_updated": self._now().isoformat(),
        }

        if save_json(self.instances_file, data):
            logger.debug("Saved plugin instances")

    def create_instance(
        self, plugin_id: str, name: str, settings: dict[str, Any]
    ) -> Optional[PluginInstance]:
        """
        Create a new plugin instance.

        Args:
            plugin_id: ID of plugin to instantiate
            name: Human-readable name for instance
            settings: Plugin-specific settings

        Returns:
            Created PluginInstance, or None if creation failed
        """
        # Validate plugin exists
        plugin = get_plugin(plugin_id)
        if plugin is None:
            logger.error(f"Plugin not found: {plugin_id}")
            return None

        # Validate settings
        is_valid, error_msg = plugin.validate_settings(settings)
        if not is_valid:
            logger.error(f"Invalid settings for {plugin_id}: {error_msg}")
            return None

        # Create instance
        instance = PluginInstance(
            id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            name=name,
            settings=settings,
            enabled=True,
            created_at=self._now(),
            updated_at=self._now(),
        )

        self._instances[instance.id] = instance
        self._save_instances()

        # Call plugin lifecycle hook
        try:
            plugin.on_enable(settings)
        except Exception as e:
            logger.warning(f"Plugin on_enable failed: {e}")

        logger.info(f"Created instance {instance.name} ({instance.id}) for plugin {plugin_id}")
        return instance

    def get_instance(self, instance_id: str) -> Optional[PluginInstance]:
        """
        Get instance by ID.

        Args:
            instance_id: Instance identifier

        Returns:
            PluginInstance if found, None otherwise
        """
        return self._instances.get(instance_id)

    def list_instances(self, plugin_id: Optional[str] = None) -> list[PluginInstance]:
        """
        List all instances, optionally filtered by plugin.

        Args:
            plugin_id: Optional plugin ID to filter by

        Returns:
            List of PluginInstance objects
        """
        instances = list(self._instances.values())

        if plugin_id:
            instances = [inst for inst in instances if inst.plugin_id == plugin_id]

        return instances

    def update_instance(
        self,
        instance_id: str,
        name: Optional[str] = None,
        settings: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing instance.

        Args:
            instance_id: Instance identifier
            name: Optional new name
            settings: Optional new settings

        Returns:
            True if updated successfully
        """
        instance = self._instances.get(instance_id)
        if instance is None:
            logger.error(f"Instance not found: {instance_id}")
            return False

        # Validate settings if provided
        if settings is not None:
            plugin = get_plugin(instance.plugin_id)
            if plugin is None:
                logger.error(f"Plugin not found: {instance.plugin_id}")
                return False

            is_valid, error_msg = plugin.validate_settings(settings)
            if not is_valid:
                logger.error(f"Invalid settings: {error_msg}")
                return False

            # Call lifecycle hook
            try:
                plugin.on_settings_change(instance.settings, settings)
            except Exception as e:
                logger.warning(f"Plugin on_settings_change failed: {e}")

            instance.settings = settings

        if name is not None:
            instance.name = name

        instance.updated_at = self._now()
        self._save_instances()

        logger.info(f"Updated instance {instance.name} ({instance_id})")
        return True

    def delete_instance(self, instance_id: str) -> bool:
        """
        Delete an instance.

        Args:
            instance_id: Instance identifier

        Returns:
            True if deleted successfully
        """
        instance = self._instances.get(instance_id)
        if instance is None:
            logger.error(f"Instance not found: {instance_id}")
            return False

        # Call lifecycle hook
        plugin = get_plugin(instance.plugin_id)
        if plugin:
            try:
                plugin.on_disable(instance.settings)
            except Exception as e:
                logger.warning(f"Plugin on_disable failed: {e}")

        del self._instances[instance_id]
        self._save_instances()

        logger.info(f"Deleted instance {instance.name} ({instance_id})")
        return True

    def enable_instance(self, instance_id: str) -> bool:
        """
        Enable an instance.

        Args:
            instance_id: Instance identifier

        Returns:
            True if enabled successfully
        """
        instance = self._instances.get(instance_id)
        if instance is None:
            logger.error(f"Instance not found: {instance_id}")
            return False

        if instance.enabled:
            return True  # Already enabled

        # Call lifecycle hook
        plugin = get_plugin(instance.plugin_id)
        if plugin:
            try:
                plugin.on_enable(instance.settings)
            except Exception as e:
                logger.warning(f"Plugin on_enable failed: {e}")

        instance.enabled = True
        instance.updated_at = self._now()
        self._save_instances()

        logger.info(f"Enabled instance {instance.name} ({instance_id})")
        return True

    def disable_instance(self, instance_id: str) -> bool:
        """
        Disable an instance.

        Args:
            instance_id: Instance identifier

        Returns:
            True if disabled successfully
        """
        instance = self._instances.get(instance_id)
        if instance is None:
            logger.error(f"Instance not found: {instance_id}")
            return False

        if not instance.enabled:
            return True  # Already disabled

        # Call lifecycle hook
        plugin = get_plugin(instance.plugin_id)
        if plugin:
            try:
                plugin.on_disable(instance.settings)
            except Exception as e:
                logger.warning(f"Plugin on_disable failed: {e}")

        instance.enabled = False
        instance.updated_at = self._now()
        self._save_instances()

        logger.info(f"Disabled instance {instance.name} ({instance_id})")
        return True

    def test_instance(
        self, instance_id: str, device_config: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Test an instance by running its generate_image method.

        Args:
            instance_id: Instance identifier
            device_config: Device configuration for image generation

        Returns:
            Tuple of (success, error_message)
        """
        instance = self._instances.get(instance_id)
        if instance is None:
            return False, f"Instance not found: {instance_id}"

        plugin = get_plugin(instance.plugin_id)
        if plugin is None:
            return False, f"Plugin not found: {instance.plugin_id}"

        try:
            image = plugin.generate_image(instance.settings, device_config)
            if image is None:
                return False, "Plugin returned None"

            logger.info(f"Test successful for instance {instance.name}")
            return True, None

        except Exception as e:
            error_msg = f"Test failed: {str(e)}"
            logger.error(f"Test failed for instance {instance.name}: {e}", exc_info=True)
            return False, error_msg

    def get_instance_count(self) -> int:
        """Get total number of instances."""
        return len(self._instances)

    def get_enabled_instances(self) -> list[PluginInstance]:
        """Get all enabled instances."""
        return [inst for inst in self._instances.values() if inst.enabled]
