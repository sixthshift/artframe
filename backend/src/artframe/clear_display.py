"""
Clear display module for graceful shutdown.
Called by systemd ExecStopPost to clear the e-ink display when service stops.
"""

import sys
from pathlib import Path


def main():
    """Clear the display on shutdown."""
    try:
        from .config import ConfigManager
        from .display.controller import DisplayController

        # Try to find config file
        config_paths = [
            Path("/opt/artframe/config/artframe-pi.yaml"),
            Path("config/artframe-pi.yaml"),
        ]

        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break

        if config_path is None:
            print("No config file found, skipping display clear")
            return 0

        config_manager = ConfigManager(config_path)
        display_config = config_manager.get_display_config()

        # Only clear if using a real display driver
        if display_config.get("driver") == "mock":
            print("Mock driver, skipping display clear")
            return 0

        controller = DisplayController(display_config)
        controller.initialize()
        controller.clear_display()
        print("Display cleared successfully")
        return 0

    except Exception as e:
        # Don't fail the service stop if we can't clear display
        print(f"Warning: Could not clear display: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
