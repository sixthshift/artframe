# Deploy to Raspberry Pi

Execute the deployment script to sync code to the Raspberry Pi for real hardware testing.

## Instructions

1. Check that `scripts/deploy-to-pi.sh` exists
2. Verify there are no uncommitted changes that might cause issues:
   - Run `git status` to show what will be deployed
   - Warn if there are unstaged changes to critical files
3. Execute the deployment script: `bash scripts/deploy-to-pi.sh`
4. Monitor the output for any errors during:
   - Connection testing
   - File sync
   - Dependency installation
   - Service restart (if applicable)
5. If deployment succeeds, remind user how to test:
   - SSH command to connect
   - Command to run artframe on the Pi
6. If deployment fails, diagnose the issue:
   - Network connectivity
   - SSH authentication
   - File permissions
   - Dependency problems

Provide clear next steps after deployment completes.
