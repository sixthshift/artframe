# Scaffold New Plugin

Generate a new plugin with complete boilerplate following Artframe plugin architecture.

## Instructions

1. Ask the user for the plugin details:
   - Plugin name (e.g., "Weather", "News Feed")
   - Brief description of what it does
   - What settings it needs (e.g., API keys, URLs, display preferences)

2. Read the base plugin class to understand the architecture:
   - Read `src/artframe/plugins/base_plugin.py`
   - Review an example plugin like `src/artframe/plugins/builtin/clock/clock.py`

3. Create the plugin structure following the pattern:
   - Create directory: `src/artframe/plugins/builtin/{plugin_name_snake_case}/`
   - Create `__init__.py` file
   - Create main plugin file: `{plugin_name_snake_case}.py`

4. Generate the plugin class with:
   - Class inheriting from `BasePlugin`
   - `__init__()` method with logger
   - `validate_settings()` with proper validation for required settings
   - `generate_image()` method with proper error handling
   - `_create_error_image()` helper for error states
   - Optional: `on_enable()`, `on_disable()` if needed for resources
   - Optional: `get_cache_key()` and `get_cache_ttl()` for caching

5. Include comprehensive docstrings:
   - Module docstring explaining the plugin
   - Class docstring with usage examples
   - Method docstrings with Args, Returns, Raises sections

6. Add helpful comments about:
   - What settings are expected
   - How the image generation works
   - Any external dependencies needed

7. Create a basic unit test file:
   - Create `tests/unit/test_{plugin_name}.py`
   - Test `validate_settings()` with valid and invalid settings
   - Test basic `generate_image()` functionality

8. Update plugin registry if needed:
   - Check `src/artframe/plugins/plugin_registry.py`
   - Add plugin to registry if manual registration is required

9. Provide user with:
   - Summary of created files
   - Example settings for testing
   - Next steps (add to requirements.txt if external deps needed)
   - How to test the plugin locally

Follow existing code style: Black formatting, type hints, proper error handling.
