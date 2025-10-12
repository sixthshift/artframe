"""
Main entry point for Artframe application.
"""

import argparse
import logging
import sys
from pathlib import Path

from .config import ConfigManager
from .controller import ArtframeController
from .logging import setup_logging


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Artframe Digital Photo Frame")

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config/artframe.yaml)",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level (default: INFO)",
    )

    parser.add_argument("--log-file", type=Path, help="Log file path (default: stdout only)")

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run web server on (default: 8000)",
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0 for network access)",
    )

    args = parser.parse_args()

    try:
        # Load configuration first
        config_manager = ConfigManager(args.config)
        logging_config = config_manager.get_logging_config()

        # Setup logging from config with CLI overrides
        setup_logging(logging_config, args.log_level, args.log_file)

        # Initialize controller
        controller = ArtframeController(args.config)

        # Skip connection tests in dev mode (check if using dev config)
        skip_tests = args.config and "dev" in str(args.config)
        controller.initialize(skip_connection_test=skip_tests)

        # Run web server with integrated scheduler
        from .web import create_app

        app = create_app(controller)
        print("🖼️  Artframe Starting...")
        print(f"📡 Web Dashboard: http://{args.host}:{args.port}")
        print("⏰ Scheduler: Active")
        print("\nPress Ctrl+C to stop")
        app.run(host=args.host, port=args.port, debug=False, threaded=True)

    except KeyboardInterrupt:
        print("\nReceived interrupt signal, exiting...")
        sys.exit(0)

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
