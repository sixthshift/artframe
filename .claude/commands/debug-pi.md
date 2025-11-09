# Debug Raspberry Pi

Remotely diagnose hardware and system issues on the Raspberry Pi.

## Instructions

1. Check connection to Pi:
   - Verify deployment script config exists in `scripts/deploy-to-pi.sh`
   - Extract `PI_HOST` from environment or use default from script
   - Test connectivity: `ping -c 1 {pi_host}`

2. If connected, gather system diagnostics via SSH:

   **System Resources:**
   - CPU usage: `ssh {pi_host} "top -bn1 | head -n 5"`
   - Memory usage: `ssh {pi_host} "free -h"`
   - Disk space: `ssh {pi_host} "df -h"`
   - System temperature: `ssh {pi_host} "vcgencmd measure_temp"` (Pi-specific)

   **Artframe Service Status:**
   - Check if service exists: `ssh {pi_host} "systemctl list-units --type=service | grep artframe"`
   - Service status: `ssh {pi_host} "systemctl status artframe"` (if exists)
   - Recent logs: `ssh {pi_host} "journalctl -u artframe -n 50 --no-pager"` (if service exists)

   **Process Information:**
   - Find Python processes: `ssh {pi_host} "ps aux | grep artframe"`
   - Network ports in use: `ssh {pi_host} "sudo netstat -tlnp | grep python"` (check web UI port)

   **Display Driver:**
   - Check GPIO permissions: `ssh {pi_host} "ls -l /dev/gpiomem"`
   - Check SPI enabled: `ssh {pi_host} "ls -l /dev/spidev*"`
   - Check I2C enabled: `ssh {pi_host} "ls -l /dev/i2c*"`

   **Python Environment:**
   - Python version: `ssh {pi_host} "python3 --version"`
   - Virtual env exists: `ssh {pi_host} "test -d ~/artframe/venv && echo 'exists' || echo 'missing'"`
   - Installed packages: `ssh {pi_host} "source ~/artframe/venv/bin/activate && pip list"`

3. Check application logs if artframe directory exists:
   - App logs: `ssh {pi_host} "tail -n 100 ~/artframe/logs/*.log"` (if logs exist)
   - Config files: `ssh {pi_host} "ls -la ~/artframe/config/"`

4. Analyze and report:
   - **Critical Issues**: Out of memory, disk full, service crashed, missing dependencies
   - **Warnings**: High CPU, approaching disk limits, old Python version
   - **Info**: Current resource usage, uptime, service status
   - **Recommendations**: Specific fixes for identified issues

5. If connection fails:
   - Check if Pi hostname is correct
   - Verify network connectivity
   - Suggest checking Pi power and network connection
   - Provide manual SSH debugging steps

Present findings in clear sections with actionable recommendations.
