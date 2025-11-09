# Verify Deployment

Verify that deployment to Raspberry Pi was successful and everything is working.

## Instructions

1. **Prerequisites Check:**
   - Confirm deployment was run recently (check last deploy output or ask user)
   - Extract Pi connection details from `scripts/deploy-to-pi.sh`
   - Verify local git status matches what should be deployed

2. **Deployment Verification:**

   **Code Sync Check:**
   - SSH to Pi and compare file checksums of critical files:
     ```
     ssh {pi_host} "cd ~/artframe && md5sum src/artframe/main.py"
     md5sum src/artframe/main.py
     ```
   - Verify directory structure exists:
     ```
     ssh {pi_host} "ls -la ~/artframe/src/artframe"
     ```

   **Dependency Check:**
   - Verify venv exists: `ssh {pi_host} "test -d ~/artframe/venv && echo 'OK' || echo 'MISSING'"`
   - Check requirements installed: `ssh {pi_host} "cd ~/artframe && source venv/bin/activate && pip check"`
   - Verify artframe is installed: `ssh {pi_host} "cd ~/artframe && source venv/bin/activate && pip show artframe"`

   **Service Health:**
   - Check if service is running: `ssh {pi_host} "systemctl is-active artframe"`
   - If running, check uptime: `ssh {pi_host} "systemctl show artframe --property=ActiveEnterTimestamp"`
   - Get recent logs: `ssh {pi_host} "journalctl -u artframe -n 20 --no-pager"`
   - Look for errors in logs: `ssh {pi_host} "journalctl -u artframe -n 100 --no-pager | grep -i error"`

3. **Functionality Tests:**

   **Web UI Access:**
   - Check if web server is listening: `ssh {pi_host} "netstat -tln | grep 8000"` (or configured port)
   - Try to fetch web UI: `curl -I http://{pi_host}:8000` (if accessible)
   - Check for HTTP 200 response

   **Display Driver:**
   - Verify display config exists: `ssh {pi_host} "cat ~/artframe/config/artframe-pi.yaml | grep display"`
   - Check for display errors in logs

   **Plugin System:**
   - Verify plugins directory: `ssh {pi_host} "ls ~/artframe/src/artframe/plugins/builtin"`
   - Check plugin data directories: `ssh {pi_host} "ls -la ~/.artframe/plugins/" 2>/dev/null || echo 'No plugin data yet'`

4. **Performance Check:**
   - Memory usage: `ssh {pi_host} "ps aux | grep python | grep artframe"`
   - Check for memory leaks (compare with baseline if available)
   - Disk usage of artframe directory: `ssh {pi_host} "du -sh ~/artframe"`

5. **Report Results:**

   **Success Criteria:**
   - ✓ All critical files synced correctly
   - ✓ Dependencies installed and up to date
   - ✓ Service running without errors (or manual process is OK)
   - ✓ Web UI accessible (if tested)
   - ✓ No critical errors in recent logs

   **Provide:**
   - Clear PASS/FAIL for each verification step
   - Any errors or warnings discovered
   - Specific commands to fix issues if found
   - Web UI URL if accessible: `http://{pi_host}:8000`
   - Next steps for manual testing

If verification fails, provide specific debugging steps and offer to run `/debug-pi` for deeper analysis.
