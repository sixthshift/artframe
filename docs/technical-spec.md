# Artframe - Technical Specification Document
*Version 3.0 - Plugin Architecture*

---

## 1. Project Overview

### Purpose
Artframe is a Raspberry Pi-based e-ink content display platform with a flexible plugin architecture. It enables users to display any type of content—photos, art, dashboards, information widgets, or custom visualizations—on e-ink displays through a unified web interface. Plugins can fetch content from any source, transform it as needed, and render optimized images for e-ink displays. The system is managed entirely through a web dashboard, eliminating the need for SSH access or command-line interaction.

### Design Philosophy
Artframe follows the **"display anything via plugins"** philosophy. Rather than being a single-purpose photo frame, Artframe provides:
- **Extensible Plugin System** - Anyone can create plugins for new content types
- **Hourly Scheduling** - Simple slot-based scheduling with weekly recurrence
- **Instance-Based Configuration** - Run multiple instances of the same plugin with different settings
- **Universal Display Pipeline** - Common display optimization for all content types
- **Developer-Friendly API** - Simple plugin interface for rapid development

### Scope
The project encompasses:
- **Plugin Architecture** - Extensible system for content generation plugins
- **Web Dashboard Interface** - Complete system management via browser
- **Slot-Based Scheduling** - Simple hourly time slots for content assignment
- **Instance Management** - Multiple configurations per plugin type
- **E-ink Display Management** - Unified display pipeline with optimization
- **Form-based Configuration** - Dynamic settings UI per plugin
- **Real-time Monitoring** - System health, plugin status, display metrics
- **Content Caching** - Efficient storage and retrieval of generated content

### Built-in Plugin Types
**Content Plugins (shipped with Artframe):**
- **Clock & Date** - Continuous time and date display with configurable formats
- **Immich Photos** - Display photos from Immich server
- **Immich Photos (AI Styled)** - Photos from Immich with optional AI style transformation
- **Quote of the Day** - Daily inspirational quote rotation
- **Word of the Day** - Vocabulary learning with definitions

### Stakeholders
| Stakeholder | Role | Interest |
|------------|------|----------|
| Primary User | System owner/administrator | Display personalized content |
| Content Viewers | Family/visitors | Enjoying displayed content |
| Plugin Developers | Community contributors | Creating new content types |
| System Maintainer | Developer | Core platform updates |

### Assumptions & Constraints
**Assumptions:**
- Raspberry Pi has stable internet connectivity (for network-based plugins)
- Plugin dependencies are manageable within Pi resource limits
- E-ink display driver is functional and compatible
- Users have basic technical knowledge for initial setup

**Constraints:**
- Limited processing power of Raspberry Pi
- E-ink display refresh rate limitations (minimize updates)
- API rate limits from external services (varies by plugin)
- Storage capacity on Raspberry Pi SD card
- Plugin execution time should be < 2 minutes

## 2. Functional Requirements

### User Stories / Use Cases

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|-------------------|----------|
| US-01 | As a user, I want to manage the frame entirely through a web interface | Can access dashboard via browser, no SSH needed | MUST |
| US-02 | As a user, I want to browse and install content plugins | Can view plugin gallery, read descriptions, install plugins | MUST |
| US-03 | As a user, I want to create multiple instances of the same plugin | Can run same plugin with different configurations (e.g., two photo albums) | MUST |
| US-04 | As a user, I want to schedule content on an hourly basis | Can assign plugin instances to time slots in a weekly schedule | MUST |
| US-05 | As a user, I want each plugin to have its own settings form | Plugin-specific settings appear dynamically in web UI | MUST |
| US-06 | As a user, I want to preview content before displaying | Can test-run plugins and see output without affecting display | SHOULD |
| US-07 | As a user, I want real-time monitoring of system health | Can view CPU, memory, temperature, plugin status, display metrics | SHOULD |
| US-08 | As a user, I want manual control over display updates | Can trigger immediate refresh or pause scheduler | MUST |
| US-09 | As a user, I want to view system and plugin logs | Can browse and filter logs via web interface | SHOULD |
| US-10 | As a developer, I want to create custom plugins easily | Can implement ContentPlugin interface and deploy | MUST |
| US-11 | As a developer, I want to test plugins independently | Can run plugin in test mode with mock display | SHOULD |
| US-12 | As a user, I want to share plugin configurations | Can export/import plugin instance settings | COULD |
| US-13 | As a user, I want content to adapt to my display dimensions | Plugins automatically optimize for configured display size | MUST |

### Core Features

1. **Plugin System Architecture**
   - Abstract base class for all content plugins
   - Automatic plugin discovery and registration
   - Dependency management per plugin
   - Isolated plugin execution environments
   - Plugin lifecycle hooks (init, execute, cleanup)
   - Settings schema validation per plugin
   - Plugin metadata (name, author, version, category)

2. **Web Dashboard Interface**
   - Multi-page navigation (Dashboard, Plugins, Schedule, Display, System)
   - Plugin gallery with search and categories
   - Instance management (create, edit, delete, duplicate)
   - Schedule timetable with drag-to-select
   - Real-time system monitoring with 1-second polling
   - Live content preview window
   - Interactive controls for scheduler and manual operations

3. **Slot-Based Scheduling**
   - 7 days × 24 hours = 168 time slots
   - Each slot can hold one plugin instance assignment
   - Bulk assignment for multiple slots at once
   - Default fallback content when no slot is assigned
   - Hour-based granularity for predictable scheduling

4. **Instance Management**
   - Multiple instances per plugin type
   - Named instances for easy identification
   - Per-instance settings persistence
   - Clone/duplicate instance configurations
   - Test mode for individual instances

6. **Display Management**
   - Real-time e-ink health monitoring
   - Aspect ratio detection and optimization
   - Universal image optimization pipeline
   - Power-efficient refresh cycles with burn-in prevention
   - Display driver abstraction (support multiple e-ink models)
   - Mock display mode for development

7. **Plugin Development Kit**
   - BasePlugin base class with lifecycle hooks
   - Display utilities library (aspect ratio, text rendering, layout helpers)
   - Settings schema definition framework
   - Test harness for plugin development
   - Example plugins with documentation
   - CLI tool for plugin scaffolding

### Edge Cases

| Scenario | Handling Strategy |
|----------|------------------|
| Plugin execution timeout | Kill plugin process, log error, wait for next scheduled slot |
| Plugin crashes during execution | Catch exception, display error image, continue schedule |
| Network connectivity loss | Display cached content, retry plugin on next cycle |
| Plugin dependency missing | Show error in plugin status, prevent instance creation |
| Invalid plugin configuration | Validate on save, prevent execution until fixed |
| Display driver crash | Automatic restart with systemd, reload last content |
| All scheduled instances fail | Display fallback error screen, alert via log |
| Corrupted plugin code | Disable plugin automatically, alert in dashboard |
| Conflicting plugin dependencies | Isolate plugins, document conflicts in plugin metadata |
| Out of disk space | Auto-purge old cache, alert user, reduce cache limits |

## 3. Non-Functional Requirements

### Performance
- Plugin execution: < 120 seconds (timeout)
- Content rendering: < 5 seconds
- Display refresh: < 2 seconds
- Web UI response time: < 200ms
- Memory usage per plugin: < 256MB
- Total system memory: < 512MB
- CPU usage: < 50% sustained
- Schedule transition: < 3 seconds

### Security
- Secure credential storage per plugin instance
- HTTPS for all external communications
- Input validation for all plugin settings and web forms
- Plugin sandboxing (limited filesystem access)
- Web server only accessible on local network (default: localhost:8000)
- CSRF protection for web forms
- Regular security updates via apt
- No authentication required (local network access assumed secure)
- Plugin code review recommendations for community plugins

### Scalability
- Support 50+ plugin instances across system
- Support 20+ active plugins simultaneously
- Queue system for plugin execution
- Efficient caching mechanism for generated content
- Configurable retention period for cached content
- Weekly recurring schedules with hourly slots

### Maintainability
- Modular plugin architecture with clear interface
- Plugin versioning and compatibility checking
- Comprehensive logging system per plugin
- Unit test coverage > 70% for core system
- Plugin test harness for developers
- Clear documentation and inline comments
- Version control with Git
- Automated update mechanism for plugins

### Compliance
- Respect external API access permissions
- Comply with third-party service terms of service
- GDPR considerations for personal data (local storage only)
- Plugin license compatibility checking
- Attribution requirements for plugins

## 4. System Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface"
        BROWSER[Web Browser]
        MOBILE[Mobile Device]
    end

    subgraph "Raspberry Pi - Artframe Core"
        subgraph "FastAPI Web Server"
            subgraph "Modular Routes"
                SPA[spa.py - SPA Serving]
                SYSTEM[system.py - Status/Config/Scheduler]
                PLUGINS[plugins.py - Plugin & Instance CRUD]
                SCHEDULES[schedules.py - Slot Management]
                DISPLAY[display.py - Display Control]
            end
            DEPS[dependencies.py - DI]
            STATIC[Static Assets - JS/CSS]
        end

        ORCHESTRATOR[Content Orchestrator]
        SCHEDULEMGR[Schedule Manager - Slot-Based]
        INSTANCEMGR[Instance Manager]
        CONFIG[Configuration Manager]
        DISPLAYCTRL[Display Controller]

        subgraph "Plugin System"
            PLUGINBASE[BasePlugin Base Class]
            PLUGINREGISTRY[Plugin Registry/Discovery]
        end

        subgraph "Built-in Plugins"
            CLOCKPLUGIN[Clock Plugin]
            IMMICHPLUGIN[Immich Plugin]
            IMMICHSTYLE[Immich Photos - AI Styled]
            QUOTEPLUGIN[Quote of the Day]
            WORDPLUGIN[Word of the Day]
        end

        subgraph "Utilities"
            DISPLAYUTILS[Display Utils]
            TEXTRENDER[Text Rendering]
            LOGGER[Domain Logger]
        end
    end

    subgraph "External Services"
        IMMICH[Immich Server]
        AI[AI Services]
        OTHER[Other APIs...]
    end

    EPAPER[E-ink Display Hardware]

    BROWSER --> SPA
    MOBILE --> SPA
    SPA --> ORCHESTRATOR
    PLUGINS --> INSTANCEMGR
    SCHEDULES --> SCHEDULEMGR
    DISPLAY --> DISPLAYCTRL

    ORCHESTRATOR --> SCHEDULEMGR
    ORCHESTRATOR --> INSTANCEMGR
    ORCHESTRATOR --> DISPLAYCTRL
    INSTANCEMGR --> PLUGINREGISTRY

    PLUGINREGISTRY --> CLOCKPLUGIN
    PLUGINREGISTRY --> IMMICHPLUGIN
    PLUGINREGISTRY --> IMMICHSTYLE
    PLUGINREGISTRY --> QUOTEPLUGIN
    PLUGINREGISTRY --> WORDPLUGIN

    DISPLAYCTRL --> EPAPER

    IMMICHPLUGIN -.-> IMMICH
    IMMICHSTYLE -.-> IMMICH
    IMMICHSTYLE -.-> AI
```

### Components & Responsibilities

| Component | Responsibility | Key Classes/Modules |
|-----------|---------------|-------------------|
| **Core System** |
| FastAPI Web Server | Web dashboard and REST APIs | `web/app.py`, `web/routes/` (modular) |
| Content Orchestrator | Plugin-driven scheduling and content display | `scheduling/content_orchestrator.py` |
| Plugin Registry | Discovery, loading, validation of plugins | `plugins/plugin_registry.py` |
| Schedule Manager | Manages slot-based time scheduling | `scheduling/schedule_manager.py` |
| Instance Manager | Manages plugin instance configs and lifecycle | `plugins/instance_manager.py` |
| Configuration Manager | System settings with env-specific configs | `config/manager.py` |
| Display Controller | Hardware abstraction for e-ink displays | `display/controller.py` |
| **Plugin System** |
| BasePlugin | Abstract base class for all plugins | `plugins/base_plugin.py` |
| Plugin Registry | Discovers and imports plugin modules | `plugins/plugin_registry.py` |
| **Built-in Plugins** |
| Clock | Continuous time and date display | `plugins/builtin/clock/` |
| Immich | Photos from Immich server | `plugins/builtin/immich/` |
| Immich Photos | AI styled photos from Immich | `plugins/builtin/immich_photos/` |
| Quote of the Day | Daily inspirational quotes | `plugins/builtin/quote_of_the_day/` |
| Word of the Day | Vocabulary learning | `plugins/builtin/word_of_the_day/` |
| **Utilities** |
| Display Utils | Aspect ratio, scaling, optimization | `utils/display_utils.py` |
| Text Rendering | Font rendering, text layout | `utils/text_render.py` |
| Domain Logger | Per-domain logging with context | `utils/logger.py` |

### Data Flow

1. **Plugin Discovery & Registration Flow:**
   - System startup triggers plugin discovery
   - Plugin Loader scans plugin directories
   - Each plugin's metadata and settings schema loaded
   - Plugins registered in Plugin Manager
   - Web UI updated with available plugins

2. **Instance Creation Flow:**
   - User selects plugin from web UI
   - User fills plugin-specific settings form
   - Settings validated against plugin schema
   - Instance Manager creates named instance with config
   - Instance appears in available content sources

3. **Content Orchestration Flow (Slot-Based):**
   - ContentOrchestrator checks current hour against schedule slots
   - If slot has assignment, resolves to plugin instance
   - Plugin's `run_active()` method invoked in dedicated thread
   - Plugin manages its own refresh loop while active
   - On hour boundary, ContentOrchestrator checks for slot change
   - If slot changes, signals current plugin to stop
   - New plugin activated for new slot

4. **Manual Content Update Flow:**
   - User clicks "Refresh" in web UI
   - API calls Orchestrator to generate new content
   - Orchestrator executes current scheduled instance immediately
   - Result displayed on e-ink

5. **Real-time Monitoring Flow:**
   - JavaScript polls system APIs every 1-3 seconds
   - APIs return: system stats, plugin status, schedule state, display metrics
   - DOM updated with current values
   - Plugin execution progress shown in real-time

## 5. Data Models & Storage

### ER Diagram

```mermaid
erDiagram
    PLUGIN {
        string id PK
        string display_name
        string version
        string description
        string plugin_class
        json settings_schema
    }

    PLUGIN_INSTANCE {
        string id PK
        string plugin_id FK
        string name
        json settings
        boolean enabled
    }

    TIME_SLOT {
        int day PK
        int hour PK
        string target_type
        string target_id FK
    }

    SCHEDULE_DEFAULT {
        string target_type
        string target_id FK
    }

    PLUGIN ||--o{ PLUGIN_INSTANCE : "has"
    PLUGIN_INSTANCE ||--o{ TIME_SLOT : "assigned to"
```

### Data Structures

```python
# Enums
class TargetType(Enum):
    INSTANCE = "instance"

# Slot-based scheduling
@dataclass
class TimeSlot:
    day: int           # 0=Monday, 6=Sunday
    hour: int          # 0-23
    target_type: str   # "instance"
    target_id: str     # ID of the plugin instance

# Plugin system models
@dataclass
class PluginMetadata:
    id: str
    display_name: str
    version: str
    description: str
    plugin_class: str
    settings_schema: Dict[str, Any]

@dataclass
class PluginInstance:
    id: str
    plugin_id: str
    name: str
    settings: Dict[str, Any]
    enabled: bool

# Content orchestration output
@dataclass
class ContentSource:
    instance: Optional[PluginInstance]
    duration_seconds: int
    source_type: str  # "schedule", "default", "none"
    source_id: Optional[str]
    source_name: Optional[str]
```

### Core APIs

| Method | Description | Return Type |
|--------|-------------|-------------|
| **Plugin Registry** |
| `discover_plugins(plugins_dir)` | Scans for plugin-info.json files | `List[PluginMetadata]` |
| `load_plugins(plugins_dir)` | Loads all plugins into registries | `None` |
| `get_plugin(plugin_id)` | Retrieves plugin instance by ID | `BasePlugin` |
| `list_plugin_metadata()` | Lists all plugin metadata | `List[PluginMetadata]` |
| **Instance Management** |
| `create_instance(plugin_id, name, settings)` | Creates plugin instance | `PluginInstance` |
| `update_instance(instance_id, settings)` | Updates instance settings | `bool` |
| `delete_instance(instance_id)` | Removes instance | `bool` |
| `list_instances(plugin_id=None)` | Lists instances, optionally filtered | `List[PluginInstance]` |
| **Schedule Management** |
| `set_slot(day, hour, target_type, target_id)` | Assign content to a time slot | `None` |
| `get_slot(day, hour)` | Get assignment for a specific slot | `Optional[TimeSlot]` |
| `get_current_slot()` | Get slot for current time | `Optional[TimeSlot]` |
| `bulk_set_slots(slots)` | Assign multiple slots at once | `None` |
| `set_default(target_type, target_id)` | Set fallback content | `None` |
| **Content Orchestration** |
| `get_current_content_source()` | Determines what to display now | `Optional[ContentSource]` |
| `should_update_display(content_source)` | Checks if refresh needed | `bool` |
| `execute_content(content_source)` | Runs plugin to generate image | `PIL.Image` |

## 6. Design Patterns & Principles

### Relevant Design Patterns

1. **Plugin Pattern (Core Architecture)**
   - **Purpose:** Enable extensible content generation system
   - **Implementation:** Abstract base class with discovery via plugin-info.json
   ```python
   class BasePlugin(ABC):
       @abstractmethod
       def generate_image(self, settings: Dict, device_config: Dict) -> PIL.Image:
           """Generate content image for display"""
           pass

       def run_active(self, display_controller, settings, device_config, stop_event) -> None:
           """Manage refresh loop while plugin is active (optional override)"""
           # Default: generate once. Plugins like Clock override for continuous updates.
           pass

       def validate_settings(self, settings: Dict) -> Tuple[bool, str]:
           """Validate plugin settings"""
           pass

       def get_cache_ttl(self, settings: Dict) -> int:
           """Return cache time-to-live in seconds"""
           return 3600  # Default 1 hour

       # Lifecycle hooks
       def on_enable(self, settings: Dict) -> None: pass
       def on_disable(self, settings: Dict) -> None: pass
       def on_settings_change(self, old: Dict, new: Dict) -> None: pass
   ```

2. **Factory Pattern**
   - **Purpose:** Create plugin instances dynamically
   - **Implementation:** Plugin factory based on plugin ID
   ```python
   class PluginFactory:
       def create_instance(self, plugin_id: str, settings: Dict) -> ContentPlugin:
           plugin_class = self._registry[plugin_id]
           return plugin_class(settings)
   ```

3. **Observer Pattern**
   - **Purpose:** React to configuration and state changes
   - **Implementation:** Event system for config updates, schedule changes

4. **Observer Pattern**
   - **Purpose:** React to configuration changes
   - **Implementation:** Event system for config updates
   ```python
   class ConfigObserver:
       def on_config_change(self, key: str, value: Any):
           pass
   ```

3. **Repository Pattern**
   - **Purpose:** Abstract data storage operations
   - **Implementation:** Repository classes for each entity type

4. **Singleton Pattern**
   - **Purpose:** Single instance of display controller
   - **Implementation:** Module-level instance management

### Justification for Patterns Chosen
- **Plugin Pattern:** Essential for requirement of swappable services
- **Observer Pattern:** Enables reactive configuration updates
- **Repository Pattern:** Decouples business logic from storage
- **Singleton Pattern:** Hardware constraint (single display)

### Error Handling & Logging Strategy

```python
# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/artframe/artframe.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['file', 'console']
    }
}

# Error handling hierarchy
class ArtframeError(Exception): pass
class SourceError(ArtframeError): pass
class StyleError(ArtframeError): pass
class DisplayError(ArtframeError): pass
```

## 7. APIs & Interfaces

### REST API Endpoints

Artframe exposes a comprehensive REST API organized by domain:

| Endpoint | Method | Description |
|----------|--------|-------------|
| **Plugin Management** (`/api/plugins/`) |
| `/api/plugins` | GET | List all available plugins |
| `/api/plugins/<id>` | GET | Get plugin details and settings schema |
| **Instance Management** (`/api/instances/`) |
| `/api/instances` | GET | List all plugin instances |
| `/api/instances` | POST | Create new plugin instance |
| `/api/instances/<id>` | GET | Get instance details |
| `/api/instances/<id>` | PUT | Update instance settings |
| `/api/instances/<id>` | DELETE | Delete instance |
| `/api/instances/<id>/enable` | POST | Enable instance |
| `/api/instances/<id>/disable` | POST | Disable instance |
| `/api/instances/<id>/test` | POST | Test run instance |
| **Schedule Management** (`/api/schedules/`) |
| `/api/schedules/slots` | GET | Get all schedule slots |
| `/api/schedules/slots` | POST | Set a single slot assignment |
| `/api/schedules/slots/bulk` | POST | Bulk set multiple slots |
| `/api/schedules/slots/<day>/<hour>` | DELETE | Clear a slot |
| `/api/schedules/default` | GET | Get default content |
| `/api/schedules/default` | POST | Set default content |
| **Display Control** (`/api/display/`) |
| `/api/display/refresh` | POST | Trigger immediate display refresh |
| `/api/display/status` | GET | Get current display status |
| **System** (`/api/system/`) |
| `/api/system/status` | GET | Get system health and stats |
| `/api/system/logs` | GET | Get recent log entries |

### Input/Output Data Formats

**Configuration Files:**
Environment-specific configuration files are used (no base config to avoid ambiguity):
- `config/artframe-laptop.yaml` - Development with mock display
- `config/artframe-pi.yaml` - Production on Raspberry Pi

**Configuration File Format (YAML):**
```yaml
artframe:
  schedule:
    update_time: "06:00"
    timezone: "Australia/Sydney"

  source:
    provider: "none"  # Plugins handle their own sources
    config: {}

  style:
    provider: "none"  # Optional AI styling per plugin
    config: {}

  display:
    driver: "mock"  # or "waveshare" for e-ink
    config:
      width: 600
      height: 448
      save_images: true
      output_dir: "./data/display_output"

  storage:
    directory: "./data/storage"

  cache:
    cache_directory: "./data/cache"
    max_size_mb: 500
    retention_days: 30

  logging:
    level: "DEBUG"
    file: "./logs/artframe.log"
```

**Runtime Data Storage:**
Plugin instances and schedules are stored as JSON in `~/.artframe/data/`:
- `plugin_instances.json` - All plugin instances with settings
- `schedules.json` - Time slot assignments and default content

### External Integrations

**Immich API Integration:**
```python
class ImmichSource(SourcePlugin):
    endpoints = {
        'albums': '/api/album',
        'photos': '/api/asset',
        'random': '/api/asset/random'
    }
    
    def fetch_photo(self) -> Photo:
        # Implementation details
        pass
```

**NanoBanana API Integration:**
```python
class NanoBananaStyle(StylePlugin):
    endpoints = {
        'transform': '/v1/transform',
        'styles': '/v1/styles',
        'status': '/v1/job/{job_id}'
    }
    
    def apply_style(self, image: bytes, style: str) -> bytes:
        # Implementation details
        pass
```

## 8. Detailed Technical Workflows

### Sequence Diagrams

**Daily Update Workflow:**
```mermaid
sequenceDiagram
    participant S as Scheduler
    participant M as Main Controller
    participant SP as Source Plugin
    participant ST as Style Plugin
    participant C as Cache Manager
    participant D as Display Controller
    
    S->>M: Trigger daily update
    M->>SP: fetch_photo()
    SP->>SP: Connect to Immich
    SP-->>M: Return Photo object
    M->>C: Check if styled version exists
    C-->>M: Not found
    M->>ST: apply_style(photo, selected_style)
    ST->>ST: Call AI service
    ST-->>M: Return styled image
    M->>C: save_styled_image()
    C-->>M: Saved successfully
    M->>D: display_image(styled_image)
    D->>D: Render to e-ink
    D-->>M: Display complete
```

### Key Algorithms / Pseudocode

**Style Selection Algorithm:**
```python
def select_style(config: Config, history: List[str]) -> str:
    """
    Select next style based on rotation strategy
    """
    strategy = config.style.rotation
    available_styles = config.style.styles
    
    if strategy == "random":
        return random.choice(available_styles)
    
    elif strategy == "sequential":
        if not history:
            return available_styles[0]
        last_index = available_styles.index(history[-1])
        next_index = (last_index + 1) % len(available_styles)
        return available_styles[next_index]
    
    elif strategy == "daily":
        # Use day of year for consistent daily rotation
        day_of_year = datetime.now().timetuple().tm_yday
        index = day_of_year % len(available_styles)
        return available_styles[index]
    
    else:
        return available_styles[0]  # Fallback
```

**Image Optimization for E-ink:**
```python
def optimize_for_eink(image: PIL.Image, display_size: Tuple[int, int]) -> PIL.Image:
    """
    Optimize image for e-ink display characteristics
    """
    # 1. Resize to display dimensions
    image = image.resize(display_size, PIL.Image.LANCZOS)
    
    # 2. Convert to grayscale if not already
    if image.mode != 'L':
        image = image.convert('L')
    
    # 3. Enhance contrast for e-ink
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    # 4. Apply dithering for better grayscale representation
    image = image.convert('1', dither=PIL.Image.FLOYDSTEINBERG)
    
    return image
```

## 9. Deployment & Infrastructure

### Environments

| Environment | Purpose | Configuration |
|------------|---------|---------------|
| Development | Local testing on desktop | Mock display, local services |
| Testing | Raspberry Pi testing | Real hardware, test services |
| Production | Daily operation | Full configuration, real services |

### CI/CD Pipeline

```yaml
# .github/workflows/artframe.yml
name: Artframe CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=artframe tests/
      
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Raspberry Pi
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.RPI_HOST }}
          username: ${{ secrets.RPI_USER }}
          key: ${{ secrets.RPI_SSH_KEY }}
          script: |
            cd /opt/artframe
            git pull origin main
            pip install -r requirements.txt
            sudo systemctl restart artframe
```

### Infrastructure-as-Code / Hosting / Cloud Details

**Raspberry Pi Setup Script:**
```bash
#!/bin/bash
# install.sh

# System dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git libjpeg-dev zlib1g-dev

# Python environment
python3 -m venv /opt/artframe/venv
source /opt/artframe/venv/bin/activate
pip install --upgrade pip

# Install application
cd /opt/artframe
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/artframe.service << EOF
[Unit]
Description=Artframe Digital Photo Frame
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/artframe
Environment="PATH=/opt/artframe/venv/bin"
ExecStart=/opt/artframe/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable artframe
sudo systemctl start artframe
```

**Resource Requirements:**
- Raspberry Pi 3B+ or newer
- 8GB+ SD card
- Stable power supply (5V, 2.5A minimum)
- Network connectivity (WiFi or Ethernet)

## 10. Testing & Quality Assurance

### Unit, Integration, End-to-End Testing

**Test Strategy:**

| Test Type | Coverage | Tools | Focus Areas |
|-----------|----------|-------|-------------|
| Unit Tests | 85% | pytest, mock | Plugin interfaces, business logic |
| Integration Tests | 70% | pytest, docker | API interactions, cache operations |
| End-to-End Tests | Manual | Physical device | Complete workflows |
| Performance Tests | Key paths | pytest-benchmark | Image processing, API calls |

**Example Test Cases:**
```python
# tests/test_source_plugin.py
def test_immich_source_fetch():
    source = ImmichSource(config)
    photo = source.fetch_photo()
    assert photo is not None
    assert photo.source_url.startswith('https://')

# tests/test_style_plugin.py
@patch('requests.post')
def test_style_application(mock_post):
    mock_post.return_value.json.return_value = {'job_id': '123'}
    style = NanoBananaStyle(config)
    result = style.apply_style(image_bytes, 'ghibli')
    assert result is not None
```

### Load/Stress Testing

| Scenario | Target | Method |
|----------|--------|--------|
| Rapid refresh requests | 10 requests/minute | Locust script |
| Large image processing | 10MB images | Memory profiling |
| Network interruption | 24-hour resilience | Chaos engineering |
| Cache overflow | 500MB limit | Automated fill test |

### Test Data Strategy

```yaml
test_data:
  images:
    - small: 100KB JPEG files
    - medium: 1MB JPEG files  
    - large: 5MB JPEG files
    - corrupted: Intentionally damaged files
  
  mock_services:
    immich:
      - success_responses
      - error_responses
      - timeout_scenarios
    
    ai_service:
      - immediate_response
      - delayed_response
      - partial_failure
```

## 11. Risks & Mitigations

### Known Risks

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| API service discontinuation | High | Medium | Plugin architecture for easy replacement |
| API rate limiting | Medium | High | Implement caching and request throttling |
| SD card corruption | High | Low | Regular backups, read-only filesystem |
| E-ink display degradation | Medium | Low | Minimize refresh cycles, gentle refresh |
| Network instability | Medium | Medium | Offline mode with cached images |
| Memory constraints | Medium | Medium | Image size limits, aggressive caching |

### Trade-offs Considered

| Decision | Trade-off | Rationale |
|----------|-----------|-----------|
| Python vs Go | Performance vs Development speed | E-ink driver availability in Python |
| Local vs Cloud processing | Privacy vs Resources | Family photos stay private |
| Daily vs Real-time updates | Freshness vs Display longevity | E-ink displays have limited refresh cycles |
| Plugin system complexity | Complexity vs Flexibility | Future-proofing is priority |

### Mitigation Strategies

1. **Service Reliability:**
   - Implement circuit breaker pattern
   - Multiple retry strategies with exponential backoff
   - Graceful degradation to cached/original images

2. **Data Integrity:**
   - Regular automated backups to external storage
   - Checksum validation for cached images
   - Configuration file versioning

3. **Performance Optimization:**
   - Lazy loading of images
   - Thumbnail generation for quick previews
   - Background processing for style transformations

## 12. Appendix

### Glossary

| Term | Definition |
|------|------------|
| E-ink | Electronic ink display technology with low power consumption |
| Immich | Self-hosted photo management solution |
| Style Transfer | AI technique to apply artistic styles to images |
| Plugin Architecture | Software design allowing modular extensions |
| GPIO | General Purpose Input/Output pins on Raspberry Pi |
| Dithering | Technique to create grayscale illusion with black/white pixels |

### References

- [Spectra 6 E-ink Display Documentation](https://example.com/spectra6-docs)
- [Immich API Documentation](https://immich.app/docs/api)
- [Raspberry Pi GPIO Documentation](https://www.raspberrypi.org/documentation/usage/gpio/)
- [Python Pillow Library](https://pillow.readthedocs.io/)
- [systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

### Future Enhancements

1. **Phase 2 Features:**
   - Web interface for remote management
   - Multi-frame slideshow mode
   - Weather/calendar overlay integration
   - Motion sensor for presence detection

2. **Phase 3 Features:**
   - Mobile app for configuration
   - Social media source integration
   - Custom style training
   - Multi-display support

3. **Long-term Considerations:**
   - Color e-ink display support
   - Voice command integration
   - AI-based photo curation
   - Distributed frame network for multiple rooms

---

*Document Version: 3.1 - Slot-Based Scheduling*
*Last Updated: November 2025*
*Author: System Architect*