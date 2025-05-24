# Recovery Instructions: How to Fix Restricted Mode

These instructions will help you recover from restricted mode and ensure your system stays in standard mode in the future.

## When Your System is Already in Restricted Mode

Yes, if your system rebuilds and ends up in restricted mode, you should run the `ensure_standard_mode.sh` script to return to standard mode. This script is specifically designed to fix systems that are already in restricted mode.

### Recovery Process:

1. **Run the enforcement script**:

   ```bash
   ./ensure_standard_mode.sh
   ```

2. **Apply environment variables to your current session**:

   ```bash
   source ~/.bashrc
   ```

3. **Restart your application to apply changes**:

   - For local development:

     ```bash
     python force_standard_mode.py
     # Then restart your application
     ```

   - For Docker environments:
     ```bash
     # Complete rebuild to apply all changes
     docker-compose down
     docker-compose up --build -d
     ```

The `ensure_standard_mode.sh` script performs multiple actions to fix restricted mode:

- Sets environment variables in multiple locations
- Creates and updates the force_standard_mode.py script
- Creates a startup hook for Docker containers
- Verifies Docker configuration
- Makes all scripts executable

## Preventing Future Restricted Mode Issues

To prevent getting into restricted mode again:

1. **Don't modify the standard mode settings**:

   - Keep `USE_RECOVERY_MODE=false` and `STANDARD_MODE=true` in your environment

2. **For Docker environments**:

   - Always use the updated Dockerfile and docker-compose.yml files
   - The modified Dockerfile enforces standard mode at the container level

3. **For VSCode**:

   - The workspace trust settings in .vscode/settings.json disable VSCode's restricted mode
   - These settings should persist across rebuilds

4. **Run periodic verification**:
   - If you notice any suspicious behavior, run the script again
   - Check your log files for "FORCE STANDARD MODE ACTIVE" message

## Emergency Recovery

If all else fails and you still end up in restricted mode:

1. **Hard reset environment variables**:

   ```bash
   export USE_RECOVERY_MODE=false
   export STANDARD_MODE=true
   ```

2. **Run force_standard_mode.py directly**:

   ```bash
   python force_standard_mode.py
   ```

3. **Restart your application with the startup hook**:
   ```bash
   ./startup_hook.sh python -m orchestrator.main
   ```

These emergency steps directly manipulate the runtime environment to force standard mode, bypassing any persistent configuration issues.
