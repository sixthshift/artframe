# Artframe Systemd Service

This directory contains the systemd service configuration for Artframe.

## Files

- **artframe.service** - Main systemd service unit file

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/sixthshift/artframe/main/backend/scripts/install.sh | sudo bash
```

To specify a different user (default is `pi`):

```bash
curl -fsSL https://raw.githubusercontent.com/sixthshift/artframe/main/backend/scripts/install.sh | sudo ARTFRAME_USER=myuser bash
```

## Manual Installation

If you need to install or update the service manually:

```bash
# Copy and customize service file
sudo sed -e "s|User=pi|User=youruser|g" \
    -e "s|Group=pi|Group=youruser|g" \
    systemd/artframe.service > /etc/systemd/system/artframe.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable artframe

# Start service
sudo systemctl start artframe
```

## Service Management

```bash
# Start service
sudo systemctl start artframe

# Stop service
sudo systemctl stop artframe

# Restart service
sudo systemctl restart artframe

# Check status
sudo systemctl status artframe

# View logs
sudo journalctl -u artframe -f

# View logs since boot
sudo journalctl -u artframe -b

# Disable autostart
sudo systemctl disable artframe

# Enable autostart
sudo systemctl enable artframe
```

## Configuration Options

### Key Settings

**Restart Policy:**
- `Restart=always` - Always restart on failure
- `RestartSec=10` - Wait 10 seconds before restart
- `StartLimitBurst=5` - Try max 5 restarts
- `StartLimitIntervalSec=600` - Within 10 minutes

**Graceful Shutdown:**
- `TimeoutStopSec=30` - Wait 30 seconds for graceful shutdown
- `KillMode=mixed` - Try SIGTERM first, then SIGKILL
- `KillSignal=SIGTERM` - Use SIGTERM for graceful shutdown
- `ExecStopPost` - Clear display after stopping

**Security:**
- `NoNewPrivileges=yes` - Cannot gain new privileges
- `PrivateTmp=yes` - Private /tmp directory
- `ProtectSystem=strict` - Read-only system directories
- `ProtectHome=yes` - Hide other users' home directories
- `ReadWritePaths` - Only these paths are writable

**Resource Limits:**
- `MemoryMax=512M` - Maximum 512MB memory
- `CPUQuota=50%` - Maximum 50% CPU usage

### Customizing the Service

The user/group can be set during installation via `ARTFRAME_USER`. For other customizations, edit the installed service file:

```bash
sudo systemctl edit artframe
```

1. **Change user/group** (if not set during install):
   ```ini
   User=myuser
   Group=mygroup
   ```

2. **Adjust restart policy:**
   ```ini
   RestartSec=30
   StartLimitBurst=3
   ```

3. **Modify resource limits:**
   ```ini
   MemoryMax=1G
   CPUQuota=100%
   ```

4. **Add environment variables:**
   ```ini
   Environment="DEBUG=1"
   Environment="ARTFRAME_CONFIG=/custom/path/config.yaml"
   ```

5. **Change working directory:**
   ```ini
   WorkingDirectory=/custom/artframe/path
   ```

## Troubleshooting

### Service won't start

```bash
# Check status for error messages
sudo systemctl status artframe

# View detailed logs
sudo journalctl -u artframe -n 50 --no-pager

# Check file permissions
ls -la /opt/artframe
ls -la /var/log/artframe
```

### Service crashes immediately

```bash
# Test manual execution
cd /opt/artframe && sudo -u pi uv run artframe

# Check Python environment
cd /opt/artframe && sudo -u pi uv run python --version
cd /opt/artframe && sudo -u pi uv pip list
```

### Display not clearing on stop

```bash
# Manually clear display
cd /opt/artframe && sudo -u pi uv run python -m artframe.clear_display

# Check ExecStopPost is configured
systemctl cat artframe | grep ExecStopPost
```

### High memory usage

```bash
# Check current memory usage
systemctl status artframe | grep Memory

# Reduce memory limit in service file
MemoryMax=256M

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart artframe
```

### Service fails after reboot

```bash
# Check if service is enabled
systemctl is-enabled artframe

# Re-enable if needed
sudo systemctl enable artframe

# Check dependencies
systemctl list-dependencies artframe
```

## Advanced Configuration

### Running on different port

Artframe port is configured in the application config, not systemd.
Edit `/opt/artframe/config/artframe.yaml`:

```yaml
web:
  host: 0.0.0.0
  port: 8080
```

### Running multiple instances

To run multiple Artframe instances (e.g., for multiple displays):

```bash
# Copy and customize service
sudo cp /etc/systemd/system/artframe.service /etc/systemd/system/artframe-living-room.service

# Edit the new service
sudo nano /etc/systemd/system/artframe-living-room.service

# Change:
# - WorkingDirectory
# - Config path
# - Ports in config file

# Enable and start
sudo systemctl enable artframe-living-room
sudo systemctl start artframe-living-room
```

### Monitoring with systemd

```bash
# Enable detailed process tracking
sudo systemctl edit artframe

# Add:
[Service]
MemoryAccounting=yes
CPUAccounting=yes
TasksAccounting=yes

# Save and reload
sudo systemctl daemon-reload
sudo systemctl restart artframe

# View resource usage
systemd-cgtop
```

## Log Management

Logs are handled by journald and logrotate.

**Logrotate configuration:** `/etc/logrotate.d/artframe`

To change log retention:

```bash
sudo nano /etc/logrotate.d/artframe

# Modify:
rotate 14  # Keep 14 days (change as needed)
```

## Related Files

- `/etc/systemd/system/artframe.service` - Installed service file
- `/etc/logrotate.d/artframe` - Log rotation config
- `/opt/artframe/` - Installation directory
- `/var/log/artframe/` - Log directory
- `/var/cache/artframe/` - Cache directory

## References

- [systemd service documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [systemd execution environment](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)
- [systemd resource control](https://www.freedesktop.org/software/systemd/man/systemd.resource-control.html)
