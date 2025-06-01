# Roo Mode Troubleshooting Guide

## Issue: Modes Appearing Then Disappearing

### What We Found and Fixed

1. **Strategy Mode Issue**: The strategy mode had been moved to the end of customModes with:
   - Empty `roleDefinition: ""`
   - Extra `source: project` field
   - This has been **FIXED** - strategy mode is now properly configured

2. **Hardcoded modes.py**: Found a file at `mcp_server/roo/modes.py` that defined different modes with old models (claude-3.7-sonnet)
   - This has been **BACKED UP** to `modes.py.backup`

3. **Protection Added**: Created scripts to protect your configuration:
   - `.roomodes.protected` - Read-only backup of correct configuration
   - `.roo/scripts/check_roomodes.sh` - Check if config has changed
   - `.roo/scripts/protect_roomodes.sh` - Re-create protection

### Why Modes Might Disappear

1. **Roo UI Overwriting**: If you make changes in Roo's UI, it might overwrite the `.roomodes` file
2. **Auto-save Features**: Some Cursor/Roo features might auto-save and modify the configuration
3. **Mode Switching**: Certain operations in Roo might trigger a config rewrite

### How to Fix When Modes Disappear

1. **Quick Fix - Restore Configuration**:
   ```bash
   cp .roomodes.protected .roomodes
   ```

2. **Check What Changed**:
   ```bash
   .roo/scripts/check_roomodes.sh
   ```

3. **Validate Configuration**:
   ```bash
   python3 .roo/scripts/validate_roomodes.py
   ```

### Prevention Tips

1. **Don't Edit Modes in Roo UI** - Only use the `.roomodes` file
2. **Don't Save Mode Settings in UI** - This can overwrite your file config
3. **Close and Reopen Roo** after any configuration changes
4. **Keep the Protected Backup** - Don't delete `.roomodes.protected`

### Current Status

✅ All 10 modes are properly configured:
- Fixed strategy mode (was missing roleDefinition)
- Removed hardcoded modes.py that was interfering
- Created protected backup of correct configuration
- All models are correctly assigned to OpenRouter

### If Problem Persists

1. Check for global Cursor/Roo configs:
   ```bash
   ls -la ~/.cursor/
   ls -la ~/.config/cursor/
   ```

2. Look for any auto-save settings in Roo and disable them

3. Monitor the .roomodes file:
   ```bash
   watch -n 1 'ls -la .roomodes'
   ```

4. After restoring, immediately close and reopen Roo

### Emergency Recovery

If all else fails, here's the complete correct configuration saved in `.roomodes.protected`. You can always restore from this backup. 