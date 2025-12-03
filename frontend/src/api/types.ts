/**
 * API Types - Re-exported from auto-generated OpenAPI types
 *
 * Run `npm run generate-types` to regenerate from backend OpenAPI spec
 */

import type { components } from './generated'

// Convenient type aliases from generated schemas
export type APIResponse = components['schemas']['APIResponse']
export type APIResponseWithData = components['schemas']['APIResponseWithData']

// Plugin types
export type Plugin = components['schemas']['PluginData']
export type PluginInstance = components['schemas']['InstanceData']
export type CreateInstanceRequest = components['schemas']['InstanceCreateRequest']
export type UpdateInstanceRequest = components['schemas']['InstanceUpdateRequest']

// Extended SettingsField with frontend-specific fields not yet in backend schema
export interface SettingsFieldOption {
  value: string
  label: string
}

export interface SettingsField {
  key: string
  type: string
  label: string
  default?: unknown
  placeholder?: string
  description?: string
  help?: string  // Alias for description
  required?: boolean
  min?: number
  max?: number
  options?: SettingsFieldOption[]
  showWhen?: {
    key: string
    value: unknown
  }
}

export interface SettingsSection {
  title: string
  fields: SettingsField[]
}

export interface SettingsSchema {
  sections: SettingsSection[]
}

// Playlist types
export type Playlist = components['schemas']['PlaylistData']
export type PlaylistItem = components['schemas']['PlaylistItemData']
export type CreatePlaylistRequest = components['schemas']['PlaylistCreateRequest']
export type UpdatePlaylistRequest = components['schemas']['PlaylistUpdateRequest']

// Schedule types
export interface ScheduleSlotData {
  target_type: 'instance' | 'playlist'
  target_id: string
}

export type ScheduleSlots = { [key: string]: ScheduleSlotData }

export interface ScheduleData {
  slots: ScheduleSlots
  slot_count: number
}

export type SlotSetRequest = components['schemas']['SlotSetRequest']
export type BulkSlotSetRequest = components['schemas']['BulkSlotSetRequest']
export type ScheduleCurrentData = components['schemas']['ScheduleCurrentData']

// Display types
export type DisplayStatus = components['schemas']['DisplayCurrentData']
export type DisplayHealth = components['schemas']['DisplayHealthData']

// System types
export type SystemInfo = components['schemas']['SystemInfoData']
export type SchedulerStatus = components['schemas']['SchedulerStatus']
export type LogEntry = components['schemas']['LogEntry']

// System status (from /api/status endpoint)
// Note: Some fields may not be present depending on backend version
export interface SystemStatus {
  // Current backend fields
  display_status?: string
  scheduler_paused?: boolean
  last_update?: string | null
  next_update?: string | null
  current_image_id?: string | null
  // Legacy fields (for backwards compatibility)
  running?: boolean
  next_scheduled?: string
  cache_stats?: {
    total_images: number
    total_size_mb: number
    oldest_image?: string
    newest_image?: string
  }
  display_state?: {
    status: string
    error_count: number
  }
}

// Connection status (from /api/connections endpoint)
// Returns a dict of service name -> connected boolean
export type ConnectionStatus = Record<string, boolean>

// Legacy type aliases for backwards compatibility
export type TimeSlot = SlotSetRequest
export type BulkSlotAssignment = BulkSlotSetRequest
export type CurrentScheduleStatus = ScheduleCurrentData

// Re-export the full generated module for advanced usage
export type { components, paths, operations } from './generated'
