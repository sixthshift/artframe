"""
Web routes for Artframe dashboard.
"""

import os
import signal
import yaml
from flask import Blueprint, render_template, jsonify, current_app, request
from typing import Dict, Any


bp = Blueprint('dashboard', __name__)


@bp.route('/')
def index():
    """Render main dashboard."""
    return render_template('dashboard.html')


@bp.route('/display')
def display_page():
    """Render display page."""
    return render_template('display.html')


@bp.route('/system')
def system_page():
    """Render system page."""
    return render_template('system.html')


@bp.route('/config')
def config_page():
    """Render configuration page."""
    return render_template('config.html')


@bp.route('/api/status')
def api_status():
    """Get current system status as JSON."""
    controller = current_app.controller

    try:
        status = controller.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/config')
def api_config():
    """Get current configuration as JSON."""
    controller = current_app.controller

    try:
        config = controller.config_manager.config
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/connections')
def api_connections():
    """Test all external connections."""
    controller = current_app.controller

    try:
        connections = controller.test_connections()
        return jsonify({
            'success': True,
            'data': connections
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/test-source', methods=['POST'])
def api_test_source():
    """Test source provider configuration."""
    try:
        data = request.get_json()

        # Extract source configuration from request
        source_config = {
            'provider': data.get('provider', 'none'),
            'config': {
                'server_url': data.get('server_url', ''),
                'api_key': data.get('api_key', ''),
                'album_id': data.get('album_id', ''),
                'selection': data.get('selection', 'random')
            }
        }

        # Create temporary source plugin to test
        from ..plugins.source import ImmichSource, NoneSource

        provider = source_config['provider']
        if provider == 'immich':
            plugin = ImmichSource(source_config['config'])
        elif provider == 'none':
            plugin = NoneSource(source_config['config'])
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown provider: {provider}'
            }), 400

        # Test configuration and connection
        if not plugin.validate_config():
            return jsonify({
                'success': False,
                'error': 'Configuration validation failed'
            })

        connection_ok = plugin.test_connection()

        return jsonify({
            'success': True,
            'connection': connection_ok,
            'message': 'Connection successful' if connection_ok else 'Connection failed'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/update', methods=['POST'])
def api_trigger_update():
    """Trigger immediate photo update."""
    controller = current_app.controller

    try:
        success = controller.manual_refresh()
        return jsonify({
            'success': success,
            'message': 'Update completed successfully' if success else 'Update failed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/clear', methods=['POST'])
def api_clear_display():
    """Clear the display."""
    controller = current_app.controller

    try:
        controller.display_controller.clear_display()
        return jsonify({
            'success': True,
            'message': 'Display cleared'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/config', methods=['PUT'])
def api_update_config():
    """Update in-memory configuration (validation only, not saved)."""
    controller = current_app.controller

    try:
        new_config = request.get_json()
        if not new_config:
            return jsonify({
                'success': False,
                'error': 'No configuration data provided'
            }), 400

        # Validate and update in-memory config
        controller.config_manager.update_config(new_config)

        return jsonify({
            'success': True,
            'message': 'Configuration updated in memory (not saved to file yet)'
        })
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid configuration: {e}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/config/save', methods=['POST'])
def api_save_config():
    """Save current in-memory configuration to YAML file."""
    controller = current_app.controller

    try:
        controller.config_manager.save_to_file(backup=True)
        return jsonify({
            'success': True,
            'message': 'Configuration saved to file. Restart required for changes to take effect.',
            'restart_required': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to save configuration: {e}'
        }), 500


@bp.route('/api/config/revert', methods=['POST'])
def api_revert_config():
    """Revert in-memory config to what's on disk."""
    controller = current_app.controller

    try:
        controller.config_manager.revert_to_file()
        return jsonify({
            'success': True,
            'message': 'Configuration reverted to saved version'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/restart', methods=['POST'])
def api_restart():
    """Restart the application."""
    try:
        # Send SIGTERM to self to trigger graceful restart
        # In production, systemd will restart the service automatically
        os.kill(os.getpid(), signal.SIGTERM)

        return jsonify({
            'success': True,
            'message': 'Restart initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/scheduler/status')
def api_scheduler_status():
    """Get scheduler status."""
    controller = current_app.controller

    try:
        status = controller.scheduler.get_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/scheduler/pause', methods=['POST'])
def api_scheduler_pause():
    """Pause automatic updates (daily e-ink refresh still occurs)."""
    controller = current_app.controller

    try:
        controller.scheduler.pause()
        return jsonify({
            'success': True,
            'message': 'Scheduler paused. Daily e-ink refresh will still occur for screen health.',
            'status': controller.scheduler.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/scheduler/resume', methods=['POST'])
def api_scheduler_resume():
    """Resume automatic updates."""
    controller = current_app.controller

    try:
        controller.scheduler.resume()
        return jsonify({
            'success': True,
            'message': 'Scheduler resumed',
            'status': controller.scheduler.get_status()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/display/current')
def api_display_current():
    """Get current display information."""
    controller = current_app.controller

    try:
        state = controller.display_controller.get_state()
        return jsonify({
            'success': True,
            'data': {
                'image_id': state.current_image_id,
                'last_update': state.last_refresh.isoformat() if state.last_refresh else None,
                'style': 'Unknown',  # TODO: Track style with image
                'status': state.status
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/display/history')
def api_display_history():
    """Get display history."""
    try:
        # TODO: Implement history tracking
        return jsonify({
            'success': True,
            'data': []
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/display/health')
def api_display_health():
    """Get e-ink display health metrics."""
    controller = current_app.controller

    try:
        state = controller.display_controller.get_state()
        return jsonify({
            'success': True,
            'data': {
                'refresh_count': 0,  # TODO: Track refresh count
                'last_refresh': state.last_refresh.isoformat() if state.last_refresh else None,
                'status': state.status,
                'error_count': state.error_count
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/source/stats')
def api_source_stats():
    """Get source statistics."""
    controller = current_app.controller

    try:
        # Basic stats for now
        return jsonify({
            'success': True,
            'data': {
                'provider': controller.config_manager.get_source_config().get('provider', 'Unknown'),
                'total_photos': 'N/A',  # TODO: Get from source plugin
                'album_name': controller.config_manager.get_source_config().get('config', {}).get('album_id', 'N/A'),
                'last_sync': 'N/A'  # TODO: Track sync time
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/system/info')
def api_system_info():
    """Get system information."""
    try:
        import psutil
        import platform
        from datetime import timedelta

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime_seconds = psutil.boot_time()
        uptime = str(timedelta(seconds=int(psutil.time.time() - uptime_seconds)))

        # Try to get temperature (Raspberry Pi)
        temp = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = round(int(f.read()) / 1000, 1)
        except:
            pass

        return jsonify({
            'success': True,
            'data': {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'disk_percent': round(disk.percent, 1),
                'temperature': temp,
                'uptime': uptime,
                'platform': platform.system()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/system/logs')
def api_system_logs():
    """Get system logs."""
    try:
        import logging
        from pathlib import Path

        level_filter = request.args.get('level', 'all')

        # TODO: Read from actual log file
        # For now, return placeholder
        return jsonify({
            'success': True,
            'data': [
                {
                    'timestamp': '2025-09-27 20:00:00',
                    'level': 'INFO',
                    'message': 'Artframe controller initialized successfully'
                },
                {
                    'timestamp': '2025-09-27 20:00:30',
                    'level': 'INFO',
                    'message': 'Starting Artframe scheduled loop'
                }
            ]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/system/logs/export')
def api_system_logs_export():
    """Export system logs as text file."""
    try:
        # TODO: Read from actual log file
        logs_text = "Artframe System Logs\n\n"
        logs_text += "2025-09-27 20:00:00 INFO Artframe controller initialized successfully\n"

        from flask import Response
        return Response(
            logs_text,
            mimetype='text/plain',
            headers={'Content-Disposition': 'attachment;filename=artframe-logs.txt'}
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500