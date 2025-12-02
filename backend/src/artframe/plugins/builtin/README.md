# Built-in Artframe Plugins

This directory contains plugins that ship with Artframe by default.

## Available Plugins

### immich_photos
Display photos from Immich server with optional AI style transformation.

**Features:**
- Fetch photos from Immich photo management server
- Optional AI artistic style transformation (Studio Ghibli, Watercolor, Oil Painting, etc.)
- Multiple photo selection modes (Random, Newest, Oldest)
- Album filtering support
- Graceful fallback to original photo if AI fails

## Plugin Structure

Each plugin follows this structure:

```
plugin_name/
├── plugin_name.py      # Main plugin class
├── plugin-info.json    # Plugin metadata
├── settings.html       # Settings form template
├── icon.png           # Plugin icon
└── README.md          # Plugin documentation (optional)
```

## Creating New Plugins

See `PLUGIN-API.md` in the project root for complete plugin development guide.

Quick start:

1. Create new directory in `builtin/` or `custom/`
2. Implement plugin class inheriting from `BasePlugin`
3. Create `plugin-info.json` with metadata
4. Add `settings.html` for configuration UI
5. Test with: `python -m artframe.plugins.test_plugin your_plugin`

## Loading Plugins

Plugins are automatically discovered and loaded from:
- `src/artframe/plugins/builtin/` - Built-in plugins
- `~/.artframe/plugins/` - User-installed plugins (future)

```python
from artframe.plugins import load_plugins, get_plugin

# Load all plugins
load_plugins(Path('src/artframe/plugins/builtin'))

# Get a plugin
plugin = get_plugin('immich_photos')

# Generate image
image = plugin.generate_image(settings, device_config)
```
