# Comprehensive Guide to Resolving VS Code Restricted Mode in GitHub Codespaces

This guide provides detailed information about VS Code Restricted Mode in GitHub Codespaces, why it occurs, and multiple strategies to permanently address it.

## Table of Contents

1. [Understanding Restricted Mode](#understanding-restricted-mode)
2. [Why Restricted Mode Occurs in Codespaces](#why-restricted-mode-occurs-in-codespaces)
3. [Solution 1: VS Code Settings](#solution-1-vs-code-settings)
4. [Solution 2: Devcontainer Configuration](#solution-2-devcontainer-configuration)
5. [Solution 3: The All-in-One Script](#solution-3-the-all-in-one-script)
6. [Solution 4: Command Line Options](#solution-4-command-line-options)
7. [Verifying Solutions](#verifying-solutions)
8. [Troubleshooting](#troubleshooting)
9. [Further Resources](#further-resources)

## Understanding Restricted Mode

Restricted Mode is a security feature in VS Code that limits functionality when working with untrusted workspaces. When activated, it disables or restricts:

- Debugging capabilities
- Task running
- Extensions with workspace access
- Terminal execution
- Source control features
- Many other features that require workspace trust

This can severely limit your ability to work effectively, especially in development environments like GitHub Codespaces where you need full access to all features.

## Why Restricted Mode Occurs in Codespaces

Restricted Mode frequently appears in GitHub Codespaces due to:

1. **Default Security Posture**: VS Code defaults to treating all new workspaces as untrusted
2. **Container Recreation**: When Codespaces containers are rebuilt or restarted, trust settings may be reset
3. **Configuration Mismatch**: Inconsistencies between user and workspace settings
4. **Extension Conflicts**: Some extensions may trigger Restricted Mode
5. **Persistent Storage Issues**: Trust settings not being properly saved to persistent storage

## Solution 1: VS Code Settings

The most direct approach is to disable workspace trust through VS Code settings. We've implemented this in `.vscode/settings.json`:

```json
{
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
```

**How it works**: This file is loaded by VS Code when opening the workspace and applies the settings automatically. It's a simple and effective solution that works across all instances of this workspace.

## Solution 2: Devcontainer Configuration

For GitHub Codespaces, configuring the devcontainer is a powerful approach. We've updated `.devcontainer/devcontainer.json` to include:

```json
"customizations": {
    "vscode": {
        "settings": {
            "security.workspace.trust.enabled": false,
            "security.workspace.trust.startupPrompt": "never",
            "security.workspace.trust.banner": "never",
            "security.workspace.trust.emptyWindow": false
        }
    }
}
```

**How it works**: When GitHub Codespaces creates a new container from this configuration, these settings are automatically applied to VS Code. This approach ensures that trust settings are baked into the container itself.

## Solution 3: The All-in-One Script

For a comprehensive solution that implements multiple approaches simultaneously, we've created `disable_restricted_mode.sh`. This script:

1. Updates or creates `.vscode/settings.json` with trust settings
2. Detects and updates the devcontainer configuration
3. Creates a VS Code API script for direct settings modification
4. Updates any `.code-workspace` files with trust settings
5. Sets environment variables to disable workspace trust

**How to use it**:

```bash
# Make it executable (if not already)
chmod +x disable_restricted_mode.sh

# Run the script
./disable_restricted_mode.sh

# Apply environment variables to current session
source ~/.bashrc
```

This script uses multiple methods to ensure Restricted Mode remains disabled even after container rebuilds or VS Code updates.

## Solution 4: Command Line Options

VS Code can be launched with command-line arguments to disable workspace trust:

```bash
code . --disable-workspace-trust
```

This works for local VS Code instances but is less applicable to Codespaces. However, we've included the environment variables in our script:

```bash
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true
```

These may help in some scenarios, especially when starting VS Code from a terminal.

## Verifying Solutions

To verify that Restricted Mode is properly disabled:

1. Look for the "Restricted Mode" indicator in the bottom right of VS Code (it should be absent)
2. Try running tasks, debugging, or using source control features
3. Check terminal functionality
4. Verify extension capabilities that require workspace trust

## Troubleshooting

If Restricted Mode persists after applying these solutions:

1. **Rebuild the Codespace**: From the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`), select "Codespaces: Rebuild Container"

2. **Check VS Code Logs**: Examine logs for clues about why trust settings aren't being applied
   - Open Command Palette
   - Select "Developer: Toggle Developer Tools"
   - Check Console for errors

3. **Extension Issues**: Some extensions may force Restricted Mode regardless of settings
   - Try temporarily disabling extensions to identify problematic ones

4. **Storage Problems**: Persistent storage issues might prevent settings from sticking
   - Try using the VS Code CLI approach in `.vscode/disable_trust.js`

5. **Direct Configuration**: If all else fails, consider using the VS Code Web Developer Console:
   - Open the Developer Tools (`F12` or `Ctrl+Shift+I`)
   - Paste and run the code from `.vscode/disable_trust.js`

## Further Resources

- [VS Code Workspace Trust Documentation](https://code.visualstudio.com/docs/editor/workspace-trust)
- [GitHub Codespaces Troubleshooting](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-creation-and-deletion-of-codespaces)
- [VS Code CLI Options](https://code.visualstudio.com/docs/editor/command-line)

---

Remember, if you're frequently encountering Restricted Mode issues, the most comprehensive solution is to use the `disable_restricted_mode.sh` script, which implements all the approaches described above.
