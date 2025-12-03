# Artframe Plugin API Specification
*Version 3.0*

---

## Overview

This document provides a complete specification for developing content plugins for Artframe. Plugins are the core extensibility mechanism that allows anyone to create custom content for e-ink displays.

**Target Audience:** Plugin developers, contributors, advanced users

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Plugin Structure](#plugin-structure)
3. [ContentPlugin Base Class](#contentplugin-base-class)
4. [Plugin Metadata](#plugin-metadata)
5. [Settings Schema](#settings-schema)
6. [Device Configuration](#device-configuration)
7. [Helper Libraries](#helper-libraries)
8. [Testing Plugins](#testing-plugins)
9. [Best Practices](#best-practices)
10. [Example Plugins](#example-plugins)

---

## Quick Start

### Minimal Plugin Example

```python
# plugins/hello_world/plugin.py
from artframe.plugins.base import ContentPlugin, PluginMetadata
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple

class HelloWorldPlugin(ContentPlugin):
    """Simple hello world plugin"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="hello_world",
            name="Hello World",
            version="1.0.0",
            author="Your Name",
            description="Displays 'Hello World' text",
            category="examples",
            dependencies=[],
            settings_schema={
                "message": {
                    "type": "string",
                    "default": "Hello World",
                    "description": "Message to display"
                }
            }
        )

    def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
        """Validate plugin settings"""
        if not settings.get("message"):
            return False, "Message cannot be empty"
        return True, ""

    def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
        """Generate content image"""
        # Create blank image
        width = device_config["width"]
        height = device_config["height"]
        image = Image.new("RGB", (width, height), color="white")

        # Draw text
        draw = ImageDraw.Draw(image)
        message = settings["message"]

        # Center text
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), message, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2

        draw.text((x, y), message, fill="black", font=font)

        return image
```

---

## Plugin Structure

### Directory Layout

```
plugins/my_plugin/
├── __init__.py              # Python package marker
├── plugin.py                # Main plugin class (required)
├── metadata.json            # Plugin metadata (optional, can be in code)
├── settings.html            # Settings form template (optional)
├── README.md               # Plugin documentation (recommended)
├── requirements.txt        # Plugin dependencies (optional)
├── assets/                 # Images, fonts, etc. (optional)
└── tests/
    └── test_plugin.py      # Unit tests (recommended)
```

### File Descriptions

**`plugin.py`** (Required)
- Contains main plugin class inheriting from `ContentPlugin`
- Must implement all abstract methods
- Entry point for plugin execution

**`metadata.json`** (Optional)
- External metadata file (alternative to code-based metadata)
- Useful for plugins with complex metadata

**`settings.html`** (Optional)
- Custom settings form with advanced controls
- Falls back to auto-generated form if not provided

**`requirements.txt`** (Optional)
- Plugin-specific Python dependencies
- Installed automatically when plugin is enabled

---

## ContentPlugin Base Class

### Abstract Methods

```python
from abc import ABC, abstractmethod
from PIL import Image
from typing import Dict, Tuple

class ContentPlugin(ABC):
    """Base class for all Artframe content plugins"""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        Return plugin metadata.

        Returns:
            PluginMetadata: Plugin information including id, name, version, etc.
        """
        pass

    @abstractmethod
    def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
        """
        Validate plugin settings before execution.

        Args:
            settings: Dictionary of plugin instance settings

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if settings are valid
            - error_message: Empty string if valid, error description if invalid
        """
        pass

    @abstractmethod
    def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
        """
        Generate content image for display.

        This is the main plugin execution method called by Artframe.

        Args:
            settings: Plugin instance settings (validated)
            device_config: Display device configuration (width, height, rotation, etc.)

        Returns:
            PIL.Image: Generated image optimized for the display

        Raises:
            RuntimeError: If content generation fails
            TimeoutError: If execution exceeds timeout (handled by framework)
        """
        pass
```

### Optional Lifecycle Methods

```python
class ContentPlugin(ABC):
    # ... abstract methods ...

    def on_enable(self, settings: Dict) -> None:
        """
        Called when plugin instance is enabled.
        Use for one-time setup, connection initialization, etc.
        """
        pass

    def on_disable(self, settings: Dict) -> None:
        """
        Called when plugin instance is disabled.
        Use for cleanup, connection closing, etc.
        """
        pass

    def on_settings_change(self, old_settings: Dict, new_settings: Dict) -> None:
        """
        Called when instance settings are updated.
        Use for reconfiguration without full restart.
        """
        pass

    def get_cache_key(self, settings: Dict) -> str:
        """
        Return unique cache key for this content.
        Override to enable intelligent caching.

        Default: Cache based on instance ID (no cache reuse between instances)
        Custom: Return key based on content (e.g., "weather_12345_2025-01-01")
        """
        return f"{self.metadata.id}_{id(settings)}"

    def get_cache_ttl(self, settings: Dict) -> int:
        """
        Return cache time-to-live in seconds.

        Returns:
            int: Seconds before cached content expires (0 = no cache)
        """
        return 0  # Default: no caching
```

---

## Plugin Metadata

### PluginMetadata Structure

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PluginMetadata:
    """Plugin metadata and configuration"""

    # Required fields
    id: str                    # Unique identifier (lowercase, underscore-separated)
    name: str                  # Display name
    version: str               # Semantic version (e.g., "1.0.0")
    author: str                # Author name or organization

    # Optional fields
    description: str = ""      # Short description (1-2 sentences)
    category: str = "other"    # Category for organization
    dependencies: List[str] = None  # Python package dependencies
    settings_schema: Dict[str, Any] = None  # Settings definition
    icon_path: str = None      # Path to plugin icon (relative to plugin dir)
    homepage: str = None       # Plugin homepage URL
    license: str = "MIT"       # License identifier
    min_artframe_version: str = "3.0.0"  # Minimum compatible version
```

### Category Values

Standard categories for plugin organization:

- `photos` - Photo display plugins
- `art` - Art and visual content
- `information` - Data displays (weather, news, etc.)
- `utilities` - System utilities
- `entertainment` - Games, fun content
- `time` - Clock and calendar displays
- `examples` - Example/demo plugins
- `other` - Uncategorized

### Example Metadata

```python
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        id="immich_photos",
        name="Immich Photos with AI Styling",
        version="1.2.0",
        author="Artframe Team",
        description="Display photos from Immich server with optional AI style transformation",
        category="photos",
        dependencies=["requests>=2.25.0"],
        settings_schema={
            # Schema defined below
        },
        icon_path="assets/icon.png",
        homepage="https://github.com/artframe/plugins/immich",
        license="MIT",
        min_artframe_version="3.0.0"
    )
```

---

## Settings Schema

### Schema Structure

Settings schema defines the configuration UI and validation rules for your plugin.

```python
settings_schema = {
    "field_name": {
        "type": "string",           # Field type (required)
        "label": "Display Label",   # UI label (optional, defaults to field_name)
        "description": "Help text", # Help text shown below field (optional)
        "default": "default_value", # Default value (optional)
        "required": True,           # Is field required? (optional, default: False)
        "validation": {...}         # Additional validation rules (optional)
    }
}
```

### Field Types

#### String
```python
"api_key": {
    "type": "string",
    "label": "API Key",
    "description": "Your service API key",
    "required": True,
    "validation": {
        "min_length": 10,
        "max_length": 100,
        "pattern": "^[A-Za-z0-9_-]+$"  # Regex pattern
    }
}
```

#### Integer
```python
"refresh_interval": {
    "type": "integer",
    "label": "Refresh Interval (minutes)",
    "default": 30,
    "validation": {
        "min": 1,
        "max": 1440
    }
}
```

#### Float
```python
"temperature_threshold": {
    "type": "float",
    "default": 20.5,
    "validation": {
        "min": -50.0,
        "max": 50.0
    }
}
```

#### Boolean
```python
"enable_feature": {
    "type": "boolean",
    "label": "Enable Advanced Features",
    "default": False
}
```

#### Enum (Select)
```python
"style": {
    "type": "enum",
    "label": "Display Style",
    "options": [
        {"value": "minimal", "label": "Minimal"},
        {"value": "detailed", "label": "Detailed"},
        {"value": "artistic", "label": "Artistic"}
    ],
    "default": "minimal"
}
```

#### URL
```python
"api_url": {
    "type": "url",
    "label": "API Endpoint",
    "default": "https://api.example.com",
    "required": True,
    "validation": {
        "schemes": ["https"],  # Only allow HTTPS
        "allow_private": False  # Disallow private IPs
    }
}
```

#### File Path
```python
"photo_directory": {
    "type": "path",
    "label": "Photo Directory",
    "description": "Path to local photo directory",
    "validation": {
        "must_exist": True,
        "type": "directory"  # or "file"
    }
}
```

#### Color
```python
"background_color": {
    "type": "color",
    "label": "Background Color",
    "default": "#FFFFFF",
    "description": "Hex color code"
}
```

#### Array
```python
"tags": {
    "type": "array",
    "label": "Filter Tags",
    "item_type": "string",
    "default": [],
    "validation": {
        "min_items": 0,
        "max_items": 10
    }
}
```

#### Object (Nested Settings)
```python
"api_config": {
    "type": "object",
    "label": "API Configuration",
    "properties": {
        "url": {"type": "url", "required": True},
        "key": {"type": "string", "required": True},
        "timeout": {"type": "integer", "default": 30}
    }
}
```

### Complete Example

```python
settings_schema = {
    "server_url": {
        "type": "url",
        "label": "Server URL",
        "description": "Your Immich server URL",
        "required": True,
        "validation": {
            "schemes": ["https", "http"]
        }
    },
    "api_key": {
        "type": "string",
        "label": "API Key",
        "required": True,
        "validation": {
            "min_length": 20
        }
    },
    "album_id": {
        "type": "string",
        "label": "Album ID",
        "description": "Specific album (leave empty for all photos)",
        "required": False
    },
    "selection_mode": {
        "type": "enum",
        "label": "Photo Selection",
        "options": [
            {"value": "random", "label": "Random"},
            {"value": "newest", "label": "Newest First"},
            {"value": "oldest", "label": "Oldest First"}
        ],
        "default": "random"
    },
    "use_ai": {
        "type": "boolean",
        "label": "Enable AI Styling",
        "default": False
    },
    "style": {
        "type": "enum",
        "label": "AI Style",
        "options": [
            {"value": "ghibli", "label": "Studio Ghibli"},
            {"value": "watercolor", "label": "Watercolor"},
            {"value": "oil", "label": "Oil Painting"}
        ],
        "default": "ghibli",
        "conditional": {
            "field": "use_ai",
            "equals": True
        }
    }
}
```

---

## Device Configuration

The `device_config` parameter provides display hardware information:

```python
device_config = {
    "width": 600,              # Display width in pixels
    "height": 448,             # Display height in pixels
    "rotation": 0,             # Display rotation (0, 90, 180, 270)
    "color_mode": "grayscale", # Color support ("color", "grayscale", "bw")
    "dpi": 150,                # Dots per inch
    "model": "spectra6",       # Display model identifier
}
```

### Using Device Config

```python
def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
    width = device_config["width"]
    height = device_config["height"]

    # Create appropriately sized image
    image = Image.new("RGB", (width, height), "white")

    # Adapt layout based on orientation
    if width > height:
        layout = self._landscape_layout(width, height)
    else:
        layout = self._portrait_layout(width, height)

    return image
```

---

## Helper Libraries

Artframe provides helper utilities for common plugin tasks.

### Display Utils

```python
from artframe.utils.display_utils import DisplayUtils

# Get display information
display_info = DisplayUtils.get_display_info(device_config)
# Returns: {
#     "width": 600,
#     "height": 448,
#     "aspect_ratio": "4:3",
#     "orientation": "landscape",
#     "megapixels": 0.27
# }

# Calculate optimal font size
font_size = DisplayUtils.calculate_font_size(
    text="Hello World",
    max_width=device_config["width"],
    max_height=device_config["height"] // 2
)

# Center an image within bounds
centered = DisplayUtils.center_image(
    image=content_image,
    target_width=device_config["width"],
    target_height=device_config["height"],
    background_color="white"
)

# Optimize image for e-ink
optimized = DisplayUtils.optimize_for_eink(
    image=content_image,
    device_config=device_config,
    enhance_contrast=True,
    dither=True
)
```

### Text Rendering

```python
from artframe.utils.text_render import TextRenderer

renderer = TextRenderer(device_config)

# Render text with auto-sizing
image = renderer.render_text(
    text="Hello World",
    font_name="Arial",
    max_width=device_config["width"] * 0.8,
    max_height=device_config["height"] * 0.3,
    color="black",
    align="center"
)

# Multi-line text with wrapping
image = renderer.render_multiline(
    text="Long text that will be wrapped automatically...",
    font_name="Arial",
    font_size=24,
    max_width=device_config["width"] - 40,
    line_spacing=1.2,
    align="left"
)

# Text with background
image = renderer.render_text_box(
    text="Important Message",
    font_size=32,
    text_color="white",
    background_color="black",
    padding=20,
    border_radius=10
)
```

### Layout Helpers

```python
from artframe.utils.layout_utils import LayoutBuilder

layout = LayoutBuilder(device_config["width"], device_config["height"])

# Grid layout
grid = layout.create_grid(rows=2, cols=2, spacing=10)
grid.place_image(image1, row=0, col=0)
grid.place_text("Label", row=1, col=0)
result = grid.render()

# Flexbox-style layout
flex = layout.create_flex(direction="vertical", spacing=20)
flex.add_item(header_image, flex=0)  # Fixed size
flex.add_item(content_image, flex=1)  # Flexible
flex.add_item(footer_image, flex=0)  # Fixed size
result = flex.render()

# Absolute positioning
canvas = layout.create_canvas()
canvas.add_image(background, x=0, y=0)
canvas.add_text("Title", x=50, y=30, font_size=48)
canvas.add_image(icon, x=device_config["width"] - 100, y=30)
result = canvas.render()
```

### HTTP Client

```python
from artframe.utils.http_client import HttpClient

# Configured HTTP client with timeouts
client = HttpClient(
    timeout=30,
    max_retries=3,
    user_agent="Artframe/3.0"
)

# GET request
response = client.get(
    url=settings["api_url"],
    headers={"X-API-Key": settings["api_key"]}
)
data = response.json()

# Download image
image_bytes = client.download(
    url=image_url,
    max_size_mb=10  # Limit download size
)
image = Image.open(BytesIO(image_bytes))

# POST request with retry
response = client.post(
    url=settings["api_url"],
    json={"query": "data"},
    retry_on_status=[500, 502, 503]
)
```

### Logging

```python
from artframe.logging import get_plugin_logger

logger = get_plugin_logger(__name__)

def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
    logger.info(f"Generating content for {self.metadata.name}")

    try:
        # Plugin logic
        logger.debug(f"Fetching data from {settings['api_url']}")
        data = self._fetch_data(settings)

        logger.info("Content generated successfully")
        return image

    except Exception as e:
        logger.error(f"Failed to generate content: {e}", exc_info=True)
        raise
```

---

## Testing Plugins

### Unit Testing

```python
# tests/test_plugin.py
import unittest
from PIL import Image
from plugins.my_plugin.plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):

    def setUp(self):
        self.plugin = MyPlugin()
        self.device_config = {
            "width": 600,
            "height": 448,
            "rotation": 0,
            "color_mode": "grayscale"
        }

    def test_metadata(self):
        """Test plugin metadata"""
        metadata = self.plugin.metadata
        self.assertEqual(metadata.id, "my_plugin")
        self.assertEqual(metadata.version, "1.0.0")

    def test_settings_validation(self):
        """Test settings validation"""
        # Valid settings
        valid, msg = self.plugin.validate_settings({"api_key": "test123"})
        self.assertTrue(valid)

        # Invalid settings
        valid, msg = self.plugin.validate_settings({})
        self.assertFalse(valid)
        self.assertIn("api_key", msg.lower())

    def test_generate_image(self):
        """Test image generation"""
        settings = {"api_key": "test123", "message": "Test"}
        image = self.plugin.generate_image(settings, self.device_config)

        # Verify image properties
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.width, self.device_config["width"])
        self.assertEqual(image.height, self.device_config["height"])

    def test_generate_image_with_mock_api(self):
        """Test with mocked external API"""
        with unittest.mock.patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"data": "test"}

            settings = {"api_key": "test123"}
            image = self.plugin.generate_image(settings, self.device_config)

            self.assertIsInstance(image, Image.Image)
            mock_get.assert_called_once()
```

### Integration Testing

```python
# tests/test_integration.py
from artframe.plugins.manager import PluginManager
from artframe.instance.manager import InstanceManager

def test_plugin_lifecycle():
    """Test full plugin lifecycle"""
    # Discover plugin
    manager = PluginManager()
    plugins = manager.discover_plugins()
    assert "my_plugin" in [p.id for p in plugins]

    # Create instance
    instance_manager = InstanceManager()
    instance = instance_manager.create_instance(
        plugin_id="my_plugin",
        name="Test Instance",
        settings={"api_key": "test123"}
    )

    # Execute plugin
    image = manager.execute_instance(instance.id, device_config)
    assert image is not None

    # Cleanup
    instance_manager.delete_instance(instance.id)
```

### Testing with Artframe CLI

```bash
# Validate plugin
artframe plugin validate plugins/my_plugin

# Test plugin execution
artframe plugin test plugins/my_plugin --settings '{"api_key": "test"}'

# Test with specific display size
artframe plugin test plugins/my_plugin --width 800 --height 600

# Profile plugin performance
artframe plugin profile plugins/my_plugin --iterations 10
```

---

## Best Practices

### Performance

1. **Minimize external API calls** - Cache responses when possible
2. **Optimize images** - Resize and compress before returning
3. **Use timeouts** - All network requests should have timeouts
4. **Lazy load resources** - Don't load fonts/assets in `__init__`
5. **Implement caching** - Override `get_cache_key()` and `get_cache_ttl()`

### Error Handling

```python
def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
    try:
        # Primary content generation
        return self._generate_primary_content(settings, device_config)

    except requests.RequestException as e:
        # Network error - show error image
        logger.warning(f"Network error, showing fallback: {e}")
        return self._generate_error_image("Network Error", device_config)

    except Exception as e:
        # Unexpected error - log and re-raise
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

### Security

1. **Validate all inputs** - Never trust settings data
2. **Sanitize file paths** - Prevent directory traversal
3. **Use HTTPS** - For all external API calls
4. **Don't log secrets** - Mask API keys in logs
5. **Limit resource usage** - Respect memory/CPU limits

```python
def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
    # Validate API key format (don't log it!)
    api_key = settings.get("api_key", "")
    if len(api_key) < 20:
        return False, "Invalid API key format"

    # Sanitize file path
    photo_dir = settings.get("photo_dir", "")
    if ".." in photo_dir or photo_dir.startswith("/"):
        return False, "Invalid directory path"

    return True, ""
```

### User Experience

1. **Clear error messages** - Tell users what went wrong and how to fix
2. **Sensible defaults** - Plugin should work with minimal configuration
3. **Helpful descriptions** - Explain what each setting does
4. **Show progress** - Log important steps for troubleshooting
5. **Graceful degradation** - Show something even if API fails

---

## Example Plugins

### Example 1: Weather Plugin

```python
# plugins/weather/plugin.py
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from artframe.plugins.base import ContentPlugin, PluginMetadata
from artframe.utils.display_utils import DisplayUtils
from artframe.utils.text_render import TextRenderer

class WeatherPlugin(ContentPlugin):

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="weather",
            name="Weather Dashboard",
            version="1.0.0",
            author="Artframe Team",
            description="Display current weather and forecast",
            category="information",
            dependencies=["requests>=2.25.0"],
            settings_schema={
                "api_key": {
                    "type": "string",
                    "label": "OpenWeatherMap API Key",
                    "required": True
                },
                "location": {
                    "type": "string",
                    "label": "Location",
                    "description": "City name or coordinates",
                    "default": "London"
                },
                "units": {
                    "type": "enum",
                    "label": "Temperature Units",
                    "options": [
                        {"value": "metric", "label": "Celsius"},
                        {"value": "imperial", "label": "Fahrenheit"}
                    ],
                    "default": "metric"
                }
            }
        )

    def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
        if not settings.get("api_key"):
            return False, "API key is required"
        if not settings.get("location"):
            return False, "Location is required"
        return True, ""

    def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
        # Fetch weather data
        weather = self._fetch_weather(settings)

        # Create image
        image = Image.new("RGB",
            (device_config["width"], device_config["height"]),
            "white"
        )
        draw = ImageDraw.Draw(image)

        # Render components
        self._draw_temperature(draw, weather, device_config)
        self._draw_conditions(draw, weather, device_config)
        self._draw_forecast(draw, weather, device_config)

        return image

    def _fetch_weather(self, settings: Dict) -> Dict:
        """Fetch weather from API"""
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": settings["location"],
            "appid": settings["api_key"],
            "units": settings["units"]
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_cache_ttl(self, settings: Dict) -> int:
        return 1800  # Cache for 30 minutes
```

### Example 2: RSS News Plugin

```python
# plugins/rss_news/plugin.py
import feedparser
from PIL import Image
from artframe.plugins.base import ContentPlugin, PluginMetadata
from artframe.utils.layout_utils import LayoutBuilder

class RSSNewsPlugin(ContentPlugin):

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="rss_news",
            name="RSS News Feed",
            version="1.0.0",
            author="Artframe Team",
            description="Display headlines from RSS feeds",
            category="information",
            dependencies=["feedparser>=6.0.0"],
            settings_schema={
                "feed_url": {
                    "type": "url",
                    "label": "RSS Feed URL",
                    "required": True
                },
                "max_items": {
                    "type": "integer",
                    "label": "Maximum Headlines",
                    "default": 5,
                    "validation": {"min": 1, "max": 10}
                }
            }
        )

    def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
        if not settings.get("feed_url"):
            return False, "Feed URL is required"
        return True, ""

    def generate_image(self, settings: Dict, device_config: Dict) -> Image.Image:
        # Parse RSS feed
        feed = feedparser.parse(settings["feed_url"])
        entries = feed.entries[:settings["max_items"]]

        # Create layout
        layout = LayoutBuilder(device_config["width"], device_config["height"])
        flex = layout.create_flex(direction="vertical", spacing=20)

        # Add title
        flex.add_text(
            text=feed.feed.title,
            font_size=32,
            font_weight="bold",
            flex=0
        )

        # Add headlines
        for entry in entries:
            flex.add_text(
                text=f"• {entry.title}",
                font_size=18,
                flex=0
            )

        return flex.render()

    def get_cache_ttl(self, settings: Dict) -> int:
        return 900  # Cache for 15 minutes
```

---

## Plugin Submission

To submit a plugin to the official Artframe plugin repository:

1. Create plugin following this specification
2. Add comprehensive README.md
3. Include tests with >70% coverage
4. Submit pull request to `artframe/plugins` repo
5. Wait for code review and approval

### Plugin Review Criteria

- ✅ Follows API specification
- ✅ Includes documentation
- ✅ Has unit tests
- ✅ No security vulnerabilities
- ✅ Reasonable performance
- ✅ Clear error messages
- ✅ Works with standard display sizes

---

*Document Version: 3.0.0*
*Last Updated: 2025-10-11*
*For Artframe v3.0+*
