# Artframe Migration Plan: To Plugin-Based Architecture
*Version 1.0*

---

## Executive Summary

This document outlines the migration strategy from the current photo-specific Artframe system to a flexible, plugin-based content display platform. The migration will be executed in phases to minimize disruption while enabling the new "display anything via plugins" vision.

**Timeline:** 8-12 weeks (depending on available development time)
**Risk Level:** Medium (requires significant refactoring but existing components can be preserved)
**Backwards Compatibility:** Phase 1 maintains current functionality

---

## Current State Analysis

### Existing Components (To Be Adapted)
```
src/artframe/
├── config/              # Configuration management ✓ (reusable)
├── controller.py        # Main orchestration ✗ (needs refactor)
├── display/            # Display drivers ✓ (reusable)
├── logging/            # Logging system ✓ (reusable)
├── models.py           # Data models ✗ (needs expansion)
├── plugins/
│   ├── source/        # Photo sources ⚠ (convert to content plugins)
│   └── style/         # AI styling ⚠ (convert to content plugin)
├── storage/           # Cache management ✓ (reusable with modification)
├── utils/             # Display utilities ✓ (reusable)
└── web/               # Web dashboard ⚠ (needs UI expansion)
```

### Current Strengths to Preserve
1. ✅ Web dashboard with real-time monitoring
2. ✅ Display driver abstraction
3. ✅ Configuration management system
4. ✅ Display utilities (aspect ratio, optimization)
5. ✅ Logging and error handling

### Current Limitations to Address
1. ❌ Hardcoded photo-only workflow
2. ❌ No plugin discovery/loading system
3. ❌ No playlist management
4. ❌ Single content source at a time
5. ❌ Tightly coupled source → style → display pipeline

---

## Migration Phases

### Phase 1: Foundation (Weeks 1-3)
**Goal:** Build plugin infrastructure while maintaining current functionality

#### Tasks
1. **Create Plugin System Core** (Week 1)
   - [ ] Design and implement `ContentPlugin` base class
   - [ ] Create `PluginManager` for discovery and loading
   - [ ] Implement plugin metadata schema
   - [ ] Build plugin validator
   - [ ] Create plugin directory structure

2. **Adapt Existing Components** (Week 2)
   - [ ] Convert `ImmichSource` to `ImmichPhotosPlugin`
   - [ ] Integrate AI styling into `ImmichPhotosPlugin`
   - [ ] Create `PluginInstance` data model
   - [ ] Implement instance configuration storage
   - [ ] Add instance management APIs

3. **Update Core Controller** (Week 3)
   - [ ] Refactor `ArtframeController` to `ContentOrchestrator`
   - [ ] Add plugin execution layer
   - [ ] Implement plugin timeout/sandboxing
   - [ ] Update cache system for generic content
   - [ ] Maintain backward compatibility mode

#### Deliverables
- ✅ Working plugin system with at least one plugin (Immich)
- ✅ Existing photo frame functionality preserved
- ✅ Plugin instance configuration via web UI

#### Testing Criteria
- [ ] Immich plugin generates same output as before
- [ ] System startup time < 10 seconds
- [ ] Plugin execution within timeout limits
- [ ] Web UI displays plugin instances

---

### Phase 2: Playlist System (Weeks 4-6)
**Goal:** Implement playlist management and rotation

#### Tasks
1. **Playlist Core** (Week 4)
   - [ ] Design `Playlist` and `PlaylistItem` data models
   - [ ] Implement `PlaylistManager`
   - [ ] Create playlist scheduler
   - [ ] Add playlist persistence (JSON/SQLite)
   - [ ] Build playlist execution engine

2. **Web UI for Playlists** (Week 5)
   - [ ] Create playlist management page
   - [ ] Add drag-and-drop playlist builder
   - [ ] Implement playlist preview
   - [ ] Add schedule configuration UI
   - [ ] Show current playlist item in dashboard

3. **Advanced Scheduling** (Week 6)
   - [ ] Implement time-based schedules
   - [ ] Add conditional display rules
   - [ ] Create playlist rotation modes (sequential, random)
   - [ ] Add manual playlist control (pause/skip)
   - [ ] Implement multi-playlist support

#### Deliverables
- ✅ Functional playlist system
- ✅ Web UI for playlist management
- ✅ Scheduled playlist execution
- ✅ Multiple content sources rotating

#### Testing Criteria
- [ ] Can create playlist with 5+ items
- [ ] Playlist rotates correctly on schedule
- [ ] Manual controls work (pause, skip, resume)
- [ ] Time-based schedules activate correctly

---

### Phase 3: Built-in Plugins (Weeks 7-9)
**Goal:** Create diverse plugin library to demonstrate platform capabilities

#### Plugin Development Priority

**High Priority (Week 7):**
- [ ] **Local Photos Plugin** - Display from filesystem directories
- [ ] **Clock/Date Plugin** - Customizable time displays
- [ ] **Weather Plugin** - Weather dashboard with forecast

**Medium Priority (Week 8):**
- [ ] **Calendar Plugin** - Daily agenda from calendar APIs
- [ ] **Quotes Plugin** - Rotating quote display
- [ ] **RSS/News Plugin** - News headlines

**Low Priority (Week 9):**
- [ ] **System Stats Plugin** - Raspberry Pi monitoring
- [ ] **Blank Screen Plugin** - For scheduled display-off periods

#### Plugin Development Template
Each plugin should include:
1. Main plugin class inheriting `ContentPlugin`
2. Settings schema with validation
3. Settings form HTML template
4. README with usage instructions
5. Example configuration
6. Unit tests

#### Deliverables
- ✅ 6-8 working plugins
- ✅ Plugin documentation
- ✅ Plugin examples for developers

#### Testing Criteria
- [ ] Each plugin executes successfully
- [ ] Plugins handle errors gracefully
- [ ] Plugin settings validate correctly
- [ ] All plugins complete within timeout

---

### Phase 4: Developer Experience (Weeks 10-11)
**Goal:** Make plugin development accessible to community

#### Tasks
1. **Plugin Development Kit** (Week 10)
   - [ ] Create plugin scaffolding CLI tool
   - [ ] Develop plugin test harness
   - [ ] Build plugin template generator
   - [ ] Create helper libraries (text rendering, layouts)
   - [ ] Document plugin API completely

2. **Documentation** (Week 11)
   - [ ] Write plugin development guide
   - [ ] Create tutorial: "Your First Plugin"
   - [ ] Document all helper utilities
   - [ ] Add troubleshooting guide
   - [ ] Create plugin submission guidelines
   - [ ] Update README with new architecture

3. **Developer Tools**
   - [ ] Add plugin debugging mode
   - [ ] Create plugin validation tool
   - [ ] Build plugin testing interface in web UI
   - [ ] Add plugin performance profiling

#### Deliverables
- ✅ Complete plugin development documentation
- ✅ CLI tools for plugin development
- ✅ Example plugins with annotated code

#### Testing Criteria
- [ ] New developer can create plugin in < 1 hour
- [ ] Plugin validation catches common errors
- [ ] Documentation covers 90%+ of use cases

---

### Phase 5: Polish & Launch (Week 12)
**Goal:** Finalize system for public release

#### Tasks
1. **Performance Optimization**
   - [ ] Profile plugin execution
   - [ ] Optimize cache management
   - [ ] Reduce memory footprint
   - [ ] Improve startup time

2. **User Experience**
   - [ ] Refine web UI design
   - [ ] Add plugin gallery/marketplace view
   - [ ] Improve error messages
   - [ ] Add guided setup wizard
   - [ ] Create demo mode

3. **Quality Assurance**
   - [ ] End-to-end testing
   - [ ] Load testing (50+ instances)
   - [ ] 7-day stability test
   - [ ] Cross-plugin compatibility testing

4. **Documentation**
   - [ ] User manual
   - [ ] Installation guide
   - [ ] FAQ
   - [ ] Video tutorials

#### Deliverables
- ✅ Production-ready system
- ✅ Complete documentation
- ✅ Stable release v3.0.0

---

## Technical Migration Strategies

### Code Refactoring Approach

#### 1. Convert Existing Plugins (Photo-Specific → Content Plugins)

**Before (Current):**
```python
class ImmichSource(SourcePlugin):
    def fetch_photo(self) -> Photo:
        # Fetch from Immich
        pass

class NanoBananaStyle(StylePlugin):
    def apply_style(self, image: bytes, style: str) -> bytes:
        # Transform image
        pass
```

**After (Plugin Architecture):**
```python
class ImmichPhotosPlugin(ContentPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="immich_photos",
            name="Immich Photos with AI Styling",
            version="1.0.0",
            category="photos",
            settings_schema={
                "immich_url": {"type": "string", "required": True},
                "api_key": {"type": "string", "required": True},
                "use_ai": {"type": "boolean", "default": False},
                "style": {"type": "string", "enum": ["ghibli", "watercolor", "oil"]}
            }
        )

    def generate_image(self, settings: Dict, device_config: Dict) -> PIL.Image:
        # Fetch photo from Immich
        photo = self._fetch_photo(settings)

        # Optionally apply AI styling
        if settings.get("use_ai"):
            photo = self._apply_ai_style(photo, settings["style"], device_config)

        # Optimize for display
        return self._optimize_for_display(photo, device_config)
```

#### 2. Controller Refactoring

**Before:**
```python
class ArtframeController:
    def daily_update(self):
        photo = self.source_plugin.fetch_photo()
        styled = self.style_plugin.apply_style(photo)
        self.display.show(styled)
```

**After:**
```python
class ContentOrchestrator:
    def execute_playlist_item(self, item: PlaylistItem) -> PIL.Image:
        # Get plugin instance
        instance = self.instance_manager.get(item.instance_id)
        plugin = self.plugin_manager.load(instance.plugin_id)

        # Execute with timeout
        image = self.plugin_executor.execute(
            plugin,
            instance.settings,
            self.device_config,
            timeout=120
        )

        # Cache result
        self.cache.save(instance.id, image)

        return image
```

### Data Migration Strategy

#### Configuration Migration
```python
def migrate_v2_to_v3_config():
    """Migrate old config to new plugin-based structure"""
    old_config = load_yaml("config/artframe.yaml")

    # Create Immich plugin instance from old source config
    immich_instance = {
        "id": "default-immich",
        "plugin_id": "immich_photos",
        "name": "Family Photos",
        "settings": {
            "immich_url": old_config["artframe"]["source"]["config"]["server_url"],
            "api_key": old_config["artframe"]["source"]["config"]["api_key"],
            "use_ai": True,
            "style": old_config["artframe"]["style"]["config"]["styles"][0]
        }
    }

    # Create default playlist
    default_playlist = {
        "id": "default",
        "name": "Main Playlist",
        "schedule_type": "time",
        "schedule_config": {
            "update_time": old_config["artframe"]["schedule"]["update_time"]
        },
        "items": [
            {"instance_id": "default-immich", "duration": 86400}
        ]
    }

    return {
        "instances": [immich_instance],
        "playlists": [default_playlist]
    }
```

---

## Risk Management

### High-Risk Items

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Plugin system complexity breaks existing functionality | High | Medium | Maintain v2 compatibility mode, extensive testing |
| Performance degradation with multiple plugins | Medium | High | Profiling, optimization, plugin execution limits |
| Plugin security vulnerabilities | High | Medium | Sandboxing, code review, dependency scanning |
| Community plugins break system | Medium | Medium | Plugin validation, versioning, safe mode |

### Rollback Strategy

Each phase should be a separate Git branch:
- `v2-stable` - Current working system
- `v3-phase1-plugins` - Phase 1 changes
- `v3-phase2-playlists` - Phase 2 changes
- etc.

If critical issues arise, can rollback to previous phase or `v2-stable`.

---

## Success Metrics

### Technical Metrics
- [ ] Plugin execution success rate > 95%
- [ ] System uptime > 99% over 30 days
- [ ] Memory usage < 512MB with 10 active plugins
- [ ] Plugin execution time < 90s average
- [ ] Web UI response time < 200ms

### User Experience Metrics
- [ ] New plugin creation time < 2 hours for developers
- [ ] User can set up playlist in < 5 minutes
- [ ] Zero SSH access needed for configuration
- [ ] Error messages are actionable 100% of time

### Community Metrics
- [ ] 5+ community-contributed plugins within 3 months
- [ ] Plugin development guide viewed 100+ times
- [ ] 10+ GitHub stars increase
- [ ] Active Discord/forum community

---

## Communication Plan

### User Communication
1. **Pre-Migration:** Announce v3.0 roadmap, solicit feedback
2. **During Migration:** Weekly updates on progress, demo videos
3. **Post-Migration:** Release announcement, migration guide, tutorial videos

### Developer Communication
1. Create `DEVELOPERS.md` with contribution guidelines
2. Set up plugin development Discord channel
3. Host live coding sessions for plugin development
4. Create plugin showcase page

---

## Appendix

### Phase 1 File Structure
```
src/artframe/
├── plugins/
│   ├── base.py              # ContentPlugin abstract class
│   ├── manager.py           # PluginManager - discovery/loading
│   ├── executor.py          # PluginExecutor - sandboxed execution
│   ├── loader.py            # Plugin file scanning
│   └── builtin/
│       └── immich_photos/
│           ├── __init__.py
│           ├── plugin.py    # ImmichPhotosPlugin class
│           ├── settings.html
│           └── metadata.json
├── instance/
│   ├── manager.py           # InstanceManager
│   └── models.py            # PluginInstance data model
├── playlist/
│   ├── manager.py           # PlaylistManager
│   ├── scheduler.py         # PlaylistScheduler
│   └── models.py            # Playlist, PlaylistItem models
├── orchestrator.py          # ContentOrchestrator (replaces controller.py)
└── cache/
    └── manager.py           # Updated for generic content
```

### Plugin Template Structure
```
plugins/my_plugin/
├── __init__.py
├── plugin.py               # Main plugin class
├── metadata.json           # Plugin metadata
├── settings.html           # Settings form template
├── README.md              # Plugin documentation
├── requirements.txt       # Plugin-specific dependencies
└── tests/
    └── test_plugin.py     # Unit tests
```

---

*Document Version: 1.0*
*Created: 2025-10-11*
*Status: Draft - Ready for Implementation*
