# Artframe Configuration Architecture

## Overview

Artframe separates configuration into **three distinct layers**:

1. **System Configuration** - Hardware and core system settings (config.yaml)
2. **Plugin Configuration** - Plugin instance settings (managed via web UI)
3. **Playlist Configuration** - Content orchestration (managed via web UI)

## 1. System Configuration (config.yaml)

System-level settings that affect the entire application. Edited via the **Config** tab in the web UI or directly in `config.yaml`.

### Location
- Default: `~/.artframe/config.yaml`
- Example: `config.example.yaml` in project root

### Settings

```yaml
artframe:
  scheduler:
    timezone: "America/New_York"
    default_duration: 3600
    refresh_interval: 86400

  display:
    driver: "spectra6"
    width: 600
    height: 448
    rotation: 0

  cache:
    cache_directory: "/var/cache/artframe"
    max_size_mb: 500
    retention_days: 30

  logging:
    level: "INFO"
    file: "/var/log/artframe/artframe.log"
    max_size_mb: 10
    backup_count: 5

  web:
    host: "0.0.0.0"
    port: 8000
    debug: false
```

## 2. Plugin Configuration

Plugin-specific settings managed through the **Plugins** tab in the web UI.

### Location
- Storage: `~/.artframe/data/plugin_instances.json`
- **Managed exclusively through web UI**

### Concept

Each **plugin instance** is a configured copy of a plugin with specific settings. You can create multiple instances of the same plugin with different configurations.

### Example: Multiple Immich Photo Instances

```
Instance 1: "Family Photos - Ghibli Style"
  - immich_url: https://immich.example.com
  - album_id: family-vacation
  - use_ai: true
  - ai_style: ghibli

Instance 2: "Family Photos - Original"
  - immich_url: https://immich.example.com
  - album_id: family-vacation
  - use_ai: false

Instance 3: "NYC Weather"
  - Plugin: weather
  - location: New York, NY
```

### Creating Plugin Instances

1. Navigate to **Plugins** tab
2. Click **Available Plugins** to see all loaded plugins
3. Click **Create Instance** on any plugin
4. Fill in the plugin-specific settings form
5. Save the instance

### Managing Instances

From the **Plugin Instances** tab, you can:
- **Edit** - Update instance settings
- **Enable/Disable** - Toggle instance on/off
- **Test** - Test run the instance
- **Delete** - Remove the instance

## 3. Playlist Configuration

Orchestrates which plugin instances run and when. Managed through the **Playlists** tab (coming soon).

### Location
- Storage: `~/.artframe/data/playlists.json`
- **Managed through web UI**

### Concept

A **playlist** is a sequence of plugin instances with timing and scheduling rules.

### Example Playlist

```
"Daily Rotation" playlist:
  - Family Photos (Ghibli) - 1 hour
  - Family Photos (Original) - 1 hour
  - Weather Dashboard - 30 minutes
  Schedule: Always running
```

## Migration from Old Configuration

**No migration is provided.** The old source/style configuration system has been completely removed in favor of the plugin architecture.

If you were using:
- `artframe.source` - Create an Immich Photos plugin instance
- `artframe.style` - Enable AI styling in the Immich Photos instance settings

## Configuration Flow

```
┌─────────────────────────────────────┐
│   1. System Config (config.yaml)   │
│   - Display hardware                │
│   - Scheduler settings              │
│   - Storage/cache                   │
│   - Logging                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   2. Plugin Instances (Web UI)      │
│   - Create instances                │
│   - Configure plugin settings       │
│   - Enable/disable instances        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   3. Playlists (Web UI)             │
│   - Arrange instances               │
│   - Set display duration            │
│   - Schedule playlists              │
└─────────────────────────────────────┘
```

## Benefits

✅ **Clear Separation** - System vs plugin configuration
✅ **Reusability** - Same instance in multiple playlists
✅ **Flexibility** - Multiple instances of same plugin
✅ **Maintainability** - Plugins define their own settings
✅ **User-Friendly** - Web UI for all plugin configuration

## Web UI Pages

### Config Tab
System-level settings only:
- Scheduler configuration
- Display hardware settings
- Storage and cache settings
- Logging configuration
- Web server settings

### Plugins Tab
Plugin management:
- **Available Plugins** - Browse and create instances
- **Plugin Instances** - Manage existing instances

### Playlists Tab (Coming Soon)
Content orchestration:
- Create playlists
- Arrange instances
- Set schedules
