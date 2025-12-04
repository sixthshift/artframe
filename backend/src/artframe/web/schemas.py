"""
Pydantic schemas for Artframe API requests and responses.

These schemas provide automatic validation and OpenAPI documentation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

# ===== Base Response Schema =====


class APIResponse(BaseModel):
    """Base API response wrapper."""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class APIResponseWithData(APIResponse):
    """API response with generic data field."""

    data: Optional[Any] = None


# ===== Status Schemas =====


class SchedulerStatus(BaseModel):
    """Scheduler status information."""

    paused: bool
    next_update: Optional[str] = None
    last_update: Optional[str] = None
    current_time: Optional[str] = None
    timezone: Optional[str] = None
    update_time: Optional[str] = None


class StatusData(BaseModel):
    """System status data."""

    display_status: str
    scheduler_paused: bool
    last_update: Optional[str] = None
    next_update: Optional[str] = None
    current_image_id: Optional[str] = None


class StatusResponse(APIResponse):
    """Response for /api/status endpoint."""

    data: Optional[StatusData] = None


# ===== Config Schemas =====


class ConfigResponse(APIResponse):
    """Response for /api/config endpoint."""

    data: Optional[dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    """Request body for updating configuration."""

    # Accept any config structure
    class Config:
        extra = "allow"


# ===== Connection Schemas =====


class ConnectionResult(BaseModel):
    """Result of a connection test."""

    name: str
    status: str
    message: Optional[str] = None


class ConnectionsResponse(APIResponse):
    """Response for /api/connections endpoint."""

    data: Optional[list[ConnectionResult]] = None


# ===== Scheduler Schemas =====


class SchedulerStatusResponse(APIResponse):
    """Response for /api/scheduler/status endpoint."""

    data: Optional[SchedulerStatus] = None
    status: Optional[SchedulerStatus] = None


# ===== Display Schemas =====


class DisplayCurrentData(BaseModel):
    """Current display information."""

    image_id: Optional[str] = None
    last_update: Optional[str] = None
    plugin_name: str = "Unknown"
    instance_name: str = "Unknown"
    status: str
    has_preview: bool
    display_count: int = 0


class DisplayCurrentResponse(APIResponse):
    """Response for /api/display/current endpoint."""

    data: Optional[DisplayCurrentData] = None


class DisplayHealthData(BaseModel):
    """Display health metrics."""

    refresh_count: int = 0
    last_refresh: Optional[str] = None
    status: str
    error_count: int = 0


class DisplayHealthResponse(APIResponse):
    """Response for /api/display/health endpoint."""

    data: Optional[DisplayHealthData] = None


# ===== Plugin Schemas =====


class SettingsField(BaseModel):
    """Schema for a single settings field."""

    key: str
    type: str
    label: str
    description: Optional[str] = None
    help: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    options: Optional[list[dict[str, Any]]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    placeholder: Optional[str] = None


class SettingsSection(BaseModel):
    """Schema for a settings section containing fields."""

    title: str
    fields: list[SettingsField] = Field(default_factory=list)


class SettingsSchema(BaseModel):
    """Schema for plugin settings with sections."""

    sections: list[SettingsSection] = Field(default_factory=list)


class PluginData(BaseModel):
    """Plugin metadata."""

    id: str
    display_name: str
    class_name: str
    description: str
    author: str
    version: str
    icon: Optional[str] = None
    settings_schema: Optional[SettingsSchema] = None


class PluginsListResponse(APIResponse):
    """Response for /api/plugins endpoint."""

    data: Optional[list[PluginData]] = None


class PluginResponse(APIResponse):
    """Response for /api/plugins/<id> endpoint."""

    data: Optional[PluginData] = None


# ===== Plugin Instance Schemas =====


class InstanceData(BaseModel):
    """Plugin instance data."""

    id: str
    plugin_id: str
    name: str
    settings: dict[str, Any] = Field(default_factory=dict)
    enabled: bool
    created_at: str
    updated_at: str


class InstancesListResponse(APIResponse):
    """Response for /api/instances endpoint."""

    data: Optional[list[InstanceData]] = None


class InstanceResponse(APIResponse):
    """Response for /api/instances/<id> endpoint."""

    data: Optional[InstanceData] = None


class InstanceCreateRequest(BaseModel):
    """Request body for creating a plugin instance."""

    plugin_id: str
    name: str
    settings: dict[str, Any] = Field(default_factory=dict)


class InstanceUpdateRequest(BaseModel):
    """Request body for updating a plugin instance."""

    name: Optional[str] = None
    settings: Optional[dict[str, Any]] = None


# ===== Schedule Schemas =====


class SlotData(BaseModel):
    """Time slot data."""

    day: int
    hour: int
    key: str
    target_type: str
    target_id: str
    target_name: str = "Unknown"
    target_details: dict[str, Any] = Field(default_factory=dict)


class ScheduleSlotsResponse(APIResponse):
    """Response for /api/schedules endpoint."""

    slots: dict[str, dict[str, Any]] = Field(default_factory=dict)
    slot_count: int = 0


class SlotSetRequest(BaseModel):
    """Request body for setting a schedule slot."""

    day: int
    hour: int
    target_type: str = "instance"
    target_id: str


class SlotSetResponse(APIResponse):
    """Response for setting a slot."""

    slot: Optional[dict[str, Any]] = None


class BulkSlotSetRequest(BaseModel):
    """Request body for bulk setting slots."""

    slots: list[SlotSetRequest]


class ScheduleCurrentData(BaseModel):
    """Current schedule information."""

    has_content: bool
    source_type: str = "none"
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    instance: Optional[dict[str, Any]] = None
    day: Optional[int] = None
    hour: Optional[int] = None


class ScheduleCurrentResponse(APIResponse):
    """Response for /api/schedules/current endpoint."""

    data: Optional[ScheduleCurrentData] = None


# ===== System Schemas =====


class SystemInfoData(BaseModel):
    """System information data."""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    temperature: Optional[float] = None
    uptime: str
    platform: str


class SystemInfoResponse(APIResponse):
    """Response for /api/system/info endpoint."""

    data: Optional[SystemInfoData] = None


class LogEntry(BaseModel):
    """Log entry data."""

    timestamp: str
    level: str
    message: str


class SystemLogsResponse(APIResponse):
    """Response for /api/system/logs endpoint."""

    data: Optional[list[LogEntry]] = None
