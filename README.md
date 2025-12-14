# Artframe

A Raspberry Pi-based digital photo frame with a modular plugin system for displaying content on e-ink displays. Supports photo sources like Immich, clocks, quotes, and AI-generated content through an extensible plugin architecture.

## Features

- **Plugin-Based Content**: Modular system supporting multiple content types (photos, clocks, quotes, AI art)
- **E-ink Display Support**: Optimized for Waveshare e-ink displays (Spectra 6, 7in3e)
- **Slot-Based Scheduling**: 7-day × 24-hour weekly schedule with one plugin per hour slot
- **Web Dashboard**: Configure plugins, manage schedules, and monitor system status
- **Multiple Plugin Instances**: Create multiple configurations per plugin type
- **Development-Friendly**: Mock display driver for development without hardware

## Quick Start

### Raspberry Pi (Production)

**One-line install:**

```bash
curl -sSL https://raw.githubusercontent.com/sixthshift/artframe/main/backend/scripts/install.sh | sudo bash
```

**Or clone and install:**

```bash
git clone https://github.com/sixthshift/artframe.git
cd artframe
sudo ./backend/scripts/install.sh
```

After installation:

1. **Configure** (edit with your settings):
   ```bash
   sudo nano /opt/artframe/config/artframe-pi.yaml
   ```

2. **Start the service**:
   ```bash
   sudo systemctl start artframe
   sudo systemctl status artframe
   ```

3. **Access the web dashboard** at `http://<pi-ip>`

### Development

1. **Setup development environment**:
   ```bash
   git clone https://github.com/sixthshift/artframe.git
   cd artframe

   # Install frontend dependencies and build
   cd frontend && npm install && npm run build && cd ..

   # Install backend with uv
   cd backend
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync --dev
   ```

2. **Run the backend**:
   ```bash
   cd backend
   uv run artframe --config config/artframe-laptop.yaml
   # Open http://localhost:8000 in browser
   ```

3. **Run tests**:
   ```bash
   cd backend
   uv run pytest tests/
   ```

4. **Run frontend dev server** (for hot-reload):
   ```bash
   cd frontend
   npm run dev
   # Frontend at http://localhost:5173, proxies API to backend
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Dashboard                            │
│              (Preact + TypeScript + Tailwind CSS)               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Web Server                         │
│    /api/plugins  /api/instances  /api/schedules  /api/display   │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐
│PluginRegistry │    │ InstanceManager  │    │ ScheduleManager  │
│               │    │                  │    │                  │
│ Discovery &   │    │ CRUD for plugin  │    │ 7×24 slot grid   │
│ Loading       │    │ configurations   │    │ Weekly schedule  │
└───────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────┐
                 │   ContentOrchestrator    │
                 │                          │
                 │ - Determines what to     │
                 │   display each hour      │
                 │ - Manages plugin threads │
                 │ - Handles transitions    │
                 └──────────────────────────┘
                                │
                                ▼
                 ┌──────────────────────────┐
                 │    DisplayController     │
                 │                          │
                 │ - MockDriver (dev)       │
                 │ - WaveshareDriver (prod) │
                 └──────────────────────────┘
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **PluginRegistry** | Discovers and loads plugins from `plugins/builtin/` |
| **InstanceManager** | Manages plugin instances (multiple configs per plugin) |
| **ScheduleManager** | Handles 7-day × 24-hour slot assignments |
| **ContentOrchestrator** | Coordinates scheduling and plugin execution |
| **DisplayController** | Manages e-ink display hardware |

## Built-in Plugins

| Plugin | Description |
|--------|-------------|
| **clock** | Digital clock with customizable time/date formats |
| **immich** | Photo display from Immich self-hosted photo server |
| **quote_of_the_day** | Daily inspirational quotes |
| **word_of_the_day** | Vocabulary learning with definitions |
| **repaint** | AI-generated art via Google Gemini |

## Configuration

Configuration is done via YAML files in `config/`.

### Example Configuration

```yaml
artframe:
  display:
    driver: mock  # or "waveshare" for production
    config:
      width: 800
      height: 480
      save_images: true
      output_dir: ./data/output

  storage:
    data_dir: ~/.artframe/data
    cache_dir: ~/.artframe/cache
    cache_max_mb: 500
    cache_retention_days: 30

  logging:
    level: DEBUG
    file: ~/.artframe/logs/artframe.log

  web:
    host: 127.0.0.1  # 0.0.0.0 for RPi
    port: 8000
    debug: true

  scheduler:
    timezone: "Australia/Sydney"
```

### Key Configuration Sections

| Section | Purpose |
|---------|---------|
| **display** | Display driver and dimensions |
| **storage** | Data and cache directories |
| **logging** | Log level and file location |
| **web** | Web server host/port |
| **scheduler** | Timezone for scheduling |

## Project Structure

```
artframe/
├── backend/
│   ├── src/artframe/
│   │   ├── plugins/              # Plugin system
│   │   │   ├── base_plugin.py    # Base class for all plugins
│   │   │   ├── plugin_registry.py
│   │   │   ├── instance_manager.py
│   │   │   └── builtin/          # Built-in plugins
│   │   │       ├── clock/
│   │   │       ├── immich/
│   │   │       ├── quote_of_the_day/
│   │   │       ├── word_of_the_day/
│   │   │       └── repaint/
│   │   ├── scheduling/           # Content orchestration
│   │   │   ├── content_orchestrator.py
│   │   │   └── schedule_manager.py
│   │   ├── display/              # Display management
│   │   │   ├── controller.py
│   │   │   └── drivers/
│   │   │       ├── mock.py
│   │   │       └── waveshare_driver.py
│   │   ├── web/                  # FastAPI web server
│   │   │   ├── app.py
│   │   │   └── routes/
│   │   ├── config/               # Configuration management
│   │   ├── storage/              # Local storage
│   │   └── main.py               # CLI entry point
│   ├── tests/
│   └── config/                   # Config files
├── frontend/
│   ├── src/
│   │   ├── pages/                # Dashboard, Plugins, Schedule, System
│   │   ├── components/
│   │   ├── api/                  # API client
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## Web API

### Plugin Management
- `GET /api/plugins` - List available plugins
- `GET /api/plugins/{id}` - Get plugin details and settings schema

### Instance Management
- `GET /api/instances` - List all instances
- `POST /api/instances` - Create new instance
- `PUT /api/instances/{id}` - Update instance
- `DELETE /api/instances/{id}` - Delete instance
- `POST /api/instances/{id}/test` - Test run instance

### Schedule Management
- `GET /api/schedules` - Get all slots
- `POST /api/schedules/slot` - Set slot
- `DELETE /api/schedules/slot` - Clear slot
- `POST /api/schedules/bulk` - Bulk set slots

### Display Control
- `GET /api/display/current` - Current display state
- `POST /api/display/refresh` - Trigger refresh

### System
- `GET /api/system/status` - System health
- `GET /api/system/info` - System information

## CLI Usage

```bash
# Development
uv run artframe --config config/artframe-laptop.yaml

# With options
artframe --config CONFIG_FILE \
         --log-level {DEBUG,INFO,WARNING,ERROR} \
         --host HOST \
         --port PORT
```

## Creating a Plugin

Each plugin needs:
1. A directory in `plugins/builtin/`
2. `plugin-info.json` with metadata and settings schema
3. Python module implementing the plugin class

### plugin-info.json

```json
{
  "id": "my_plugin",
  "display_name": "My Plugin",
  "class": "MyPlugin",
  "description": "Description of my plugin",
  "version": "1.0.0",
  "settings_schema": {
    "sections": [
      {
        "title": "Settings",
        "fields": [
          {
            "key": "option",
            "type": "select",
            "label": "Option",
            "options": [
              {"value": "a", "label": "Option A"},
              {"value": "b", "label": "Option B"}
            ]
          }
        ]
      }
    ]
  }
}
```

### Plugin Class

```python
from artframe.plugins.base_plugin import BasePlugin
from PIL import Image

class MyPlugin(BasePlugin):
    def generate_image(
        self,
        settings: dict,
        device_config: dict
    ) -> Image.Image:
        """Generate content image."""
        width = device_config.get("width", 800)
        height = device_config.get("height", 480)

        image = Image.new("RGB", (width, height), "white")
        # Draw content...
        return image

    def get_refresh_interval(self, settings: dict) -> int:
        """Return seconds between refreshes."""
        return 3600  # 1 hour
```

## Hardware Setup

### Supported E-ink Displays

| Display | Resolution | Driver |
|---------|------------|--------|
| Spectra 6 | 600×448 | waveshare |
| 7in3e | 800×480 | waveshare |
| Mock | Configurable | mock |

### Raspberry Pi GPIO Connections (Waveshare)

| Display Pin | Pi GPIO | Function |
|-------------|---------|----------|
| BUSY | 24 | Busy signal |
| RST | 17 | Reset |
| DC | 25 | Data/Command |
| CS | 8 | Chip Select |
| CLK | 11 | SPI Clock |
| DIN | 10 | SPI Data |

### Enable SPI

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
```

## Data Storage

Artframe stores data in `~/.artframe/`:

| Path | Purpose |
|------|---------|
| `data/plugin_instances.json` | Plugin instance configurations |
| `data/schedules.json` | Schedule slot assignments |
| `cache/` | Cached images and data |
| `logs/` | Application logs |

## Troubleshooting

### Common Issues

1. **SPI Permission Errors**:
   ```bash
   sudo usermod -a -G spi pi
   # Reboot required
   ```

2. **Display Not Updating**:
   - Check GPIO connections
   - Verify SPI is enabled
   - Check logs: `journalctl -u artframe -f`

3. **Plugin Not Loading**:
   - Verify `plugin-info.json` is valid JSON
   - Check plugin class name matches `"class"` field
   - Check logs for import errors

### Logs and Debugging

```bash
# Service logs
journalctl -u artframe -f

# Application logs
tail -f ~/.artframe/logs/artframe.log

# Debug mode
artframe --log-level DEBUG --config config/artframe-laptop.yaml
```

## Development

### Running Tests

```bash
cd backend

# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# With coverage
uv run pytest --cov=src/artframe
```

### Code Quality

```bash
cd backend

# Format code
uv run ruff format src/ tests/

# Lint
uv run ruff check src/ tests/

# Type checking
uv run mypy src/artframe
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `uv run pytest`
6. Format code: `uv run ruff format src/ tests/`
7. Commit changes: `git commit -m "Add amazing feature"`
8. Push to branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Immich](https://immich.app/) for self-hosted photo management
- [Waveshare](https://www.waveshare.com/) for e-ink display hardware
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Preact](https://preactjs.com/) for the lightweight frontend
