# Artframe 🎨📷

A Raspberry Pi-based digital photo frame that automatically retrieves daily photos from your photo management system (like Immich), applies beautiful AI-powered artistic styles, and displays them on an e-ink display.

## Features ✨

- **Automated Photo Retrieval**: Connects to Immich (or other photo sources) to fetch your photos
- **AI Style Transformation**: Uses AI services like NanoBanana to apply artistic styles (Studio Ghibli, watercolor, oil painting, etc.)
- **E-ink Display Support**: Optimized for e-ink displays like Spectra 6 with power-efficient refresh cycles
- **Modular Plugin Architecture**: Easy to add new photo sources and AI style services
- **Smart Caching**: Local caching system with automatic cleanup and size management
- **Configurable Scheduling**: Daily updates at your preferred time with multiple rotation strategies
- **Development-Friendly**: Mock drivers and comprehensive testing for easy development

## Quick Start 🚀

### For Raspberry Pi (Production)

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/artframe.git
   cd artframe
   sudo ./scripts/setup_artframe.sh
   ```

2. **Configure**:
   ```bash
   sudo nano /opt/artframe/config/artframe.yaml
   # Add your API keys and settings
   ```

3. **Start the service**:
   ```bash
   sudo systemctl start artframe
   sudo systemctl status artframe
   ```

### For Development

1. **Setup development environment**:
   ```bash
   git clone https://github.com/yourusername/artframe.git
   cd artframe

   # Install in development mode with all dependencies
   pip install -e .[dev]
   ```

2. **Configure for development**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run tests**:
   ```bash
   pytest tests/
   ```

4. **Test manually**:
   ```bash
   python -m artframe --config config/artframe-dev.yaml test
   python -m artframe --config config/artframe-dev.yaml update
   ```

5. **Run web dashboard**:
   ```bash
   python -m artframe serve --port 5000
   # Open http://localhost:5000 in browser
   ```

## Configuration 📋

Configuration is done via YAML files. See `config/artframe.yaml` for production settings and `config/artframe-dev.yaml` for development.

### Key Configuration Sections

- **Source**: Photo retrieval settings (Immich server, API keys, album selection)
- **Style**: AI transformation settings (NanoBanana API, available styles, rotation strategy)
- **Display**: E-ink display settings (GPIO pins, rotation, metadata overlay)
- **Cache**: Local storage settings (directory, size limits, retention)
- **Schedule**: Update timing (daily schedule, timezone)

### Example Configuration

```yaml
artframe:
  schedule:
    update_time: "06:00"
    timezone: "America/New_York"

  source:
    provider: "immich"
    config:
      server_url: "https://your-immich-server.com"
      api_key: "${IMMICH_API_KEY}"
      album_id: "family-photos"
      selection: "random"

  style:
    provider: "nanobanana"
    config:
      api_url: "https://api.nanobanana.com"
      api_key: "${NANOBANANA_API_KEY}"
      styles: ["ghibli", "watercolor", "oil_painting"]
      rotation: "daily"

  display:
    driver: "spectra6"
    config:
      gpio_pins:
        busy: 24
        reset: 17
        dc: 25
        cs: 8
```

## Architecture 🏗️

Artframe follows a modular plugin architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Source Plugin │    │   Style Plugin   │    │ Display Driver  │
│   (Immich, etc) │    │ (NanoBanana,etc) │    │ (Spectra6,Mock) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │ Main Controller     │
                    │ - Scheduling        │
                    │ - Workflow          │
                    │ - Error Handling    │
                    └─────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │ Cache Manager       │
                    │ - Image Storage     │
                    │ - Cleanup           │
                    │ - Statistics        │
                    └─────────────────────┘
```

## Usage Examples 💡

### Command Line Interface

```bash
# Run the main scheduled loop
artframe run

# Trigger immediate photo update
artframe update

# Check system status
artframe status

# Test connections to external services
artframe test

# Clear the display
artframe clear

# Run web dashboard
artframe serve --port 5000
```

### Programmatic Usage

```python
from artframe.controller import ArtframeController

# Initialize controller
controller = ArtframeController("config/artframe.yaml")
controller.initialize()

# Manual photo update
success = controller.manual_refresh()

# Get system status
status = controller.get_status()
print(f"Last update: {status['last_update']}")
print(f"Cache size: {status['cache_stats']['total_size_mb']} MB")
```

## Hardware Setup 🔧

### Supported E-ink Displays

- **Spectra 6**: 600x448 pixel e-ink display with SPI interface
- **Mock Driver**: For development without hardware

### Raspberry Pi GPIO Connections (Spectra 6)

| Display Pin | Pi GPIO | Function |
|-------------|---------|----------|
| BUSY        | 24      | Busy signal |
| RST         | 17      | Reset |
| DC          | 25      | Data/Command |
| CS          | 8       | Chip Select |
| CLK         | 11      | SPI Clock |
| DIN         | 10      | SPI Data |

### Enable SPI

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
```

## Development 👨‍💻

### Project Structure

```
artframe/
├── src/artframe/           # Main source code
│   ├── plugins/           # Plugin system (source, style)
│   ├── display/           # Display management
│   ├── cache/             # Cache management
│   ├── config/            # Configuration system
│   └── utils/             # Utilities (scheduler, etc)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── config/                # Configuration files
├── scripts/               # Setup and utility scripts
└── examples/              # Example code
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src/artframe

# Specific test file
pytest tests/unit/test_config.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Type checking
mypy src/artframe

# Security scan
bandit -r src/
```

### Adding New Plugins

1. **Source Plugin** (for new photo sources):
   ```python
   from artframe.plugins.source.base import SourcePlugin

   class MySourcePlugin(SourcePlugin):
       def fetch_photo(self) -> Photo:
           # Implement photo fetching logic
           pass
   ```

2. **Style Plugin** (for new AI services):
   ```python
   from artframe.plugins.style.base import StylePlugin

   class MyStylePlugin(StylePlugin):
       def apply_style(self, image_path, style, output_path) -> bool:
           # Implement style transformation logic
           pass
   ```

## Troubleshooting 🔍

### Common Issues

1. **SPI Permission Errors**:
   ```bash
   sudo usermod -a -G spi pi
   # Reboot required
   ```

2. **Display Not Updating**:
   - Check GPIO connections
   - Verify SPI is enabled
   - Check service logs: `journalctl -u artframe -f`

3. **API Connection Issues**:
   ```bash
   artframe test  # Test all connections
   ```

4. **Cache Issues**:
   ```bash
   # Clear cache
   sudo rm -rf /var/cache/artframe/*
   sudo systemctl restart artframe
   ```

### Logs and Debugging

```bash
# Service logs
journalctl -u artframe -f

# Application logs
tail -f /var/log/artframe/artframe.log

# Debug mode
artframe --log-level DEBUG run
```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Format code: `black src/ tests/`
7. Commit changes: `git commit -m "Add amazing feature"`
8. Push to branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 👏

- [Immich](https://immich.app/) for photo management
- [NanoBanana](https://nanobanana.com/) for AI style transformations
- [Waveshare](https://www.waveshare.com/) for e-ink display hardware
- The Raspberry Pi Foundation for amazing hardware

---

Made with ❤️ for digital art and family memories