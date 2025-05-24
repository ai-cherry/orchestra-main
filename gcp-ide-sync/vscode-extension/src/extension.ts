import * as vscode from "vscode";
import { GcpWorkstationProvider } from "./providers/gcpWorkstationProvider";
import { GcpAuthManager } from "./auth/gcpAuthManager";
import { FileSync } from "./sync/fileSync";
import { TerminalManager } from "./terminal/terminalManager";
import { StatusBarManager } from "./ui/statusBarManager";

// Extension activation context
export async function activate(context: vscode.ExtensionContext) {
  console.log("GCP IDE Sync extension is now active");

  // Initialize authentication manager
  const authManager = new GcpAuthManager(context);

  // Initialize file synchronization
  const fileSync = new FileSync(context, authManager);

  // Initialize terminal manager
  const terminalManager = new TerminalManager(context, authManager);

  // Initialize status bar
  const statusBar = new StatusBarManager(context);

  // Initialize tree view provider
  const workstationProvider = new GcpWorkstationProvider(context, authManager);
  vscode.window.registerTreeDataProvider(
    "gcp-ide-sync-explorer",
    workstationProvider,
  );

  // Register commands
  const commands = [
    vscode.commands.registerCommand("gcp-ide-sync.connect", async () => {
      try {
        const authenticated = await authManager.authenticate();
        if (authenticated) {
          await fileSync.initialSync();
          statusBar.setConnected();
          vscode.window.showInformationMessage("Connected to GCP Workstation");
        }
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to connect: ${error}`);
      }
    }),

    vscode.commands.registerCommand("gcp-ide-sync.disconnect", async () => {
      try {
        await fileSync.stopSync();
        await terminalManager.closeAllTerminals();
        statusBar.setDisconnected();
        vscode.window.showInformationMessage(
          "Disconnected from GCP Workstation",
        );
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to disconnect: ${error}`);
      }
    }),

    vscode.commands.registerCommand("gcp-ide-sync.syncFiles", async () => {
      try {
        await fileSync.manualSync();
        vscode.window.showInformationMessage("Files synchronized successfully");
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to sync files: ${error}`);
      }
    }),

    vscode.commands.registerCommand("gcp-ide-sync.openTerminal", async () => {
      try {
        await terminalManager.openTerminal();
      } catch (error) {
        vscode.window.showErrorMessage(`Failed to open terminal: ${error}`);
      }
    }),

    vscode.commands.registerCommand(
      "gcp-ide-sync.startWorkstation",
      async (workstationId: string) => {
        try {
          await workstationProvider.startWorkstation(workstationId);
          vscode.window.showInformationMessage(
            `Starting workstation ${workstationId}`,
          );
        } catch (error) {
          vscode.window.showErrorMessage(
            `Failed to start workstation: ${error}`,
          );
        }
      },
    ),

    vscode.commands.registerCommand(
      "gcp-ide-sync.stopWorkstation",
      async (workstationId: string) => {
        try {
          await workstationProvider.stopWorkstation(workstationId);
          vscode.window.showInformationMessage(
            `Stopping workstation ${workstationId}`,
          );
        } catch (error) {
          vscode.window.showErrorMessage(
            `Failed to stop workstation: ${error}`,
          );
        }
      },
    ),
  ];

  // Add commands to subscriptions
  commands.forEach((command) => context.subscriptions.push(command));

  // Add event listeners
  const fileWatcher = vscode.workspace.createFileSystemWatcher("**/*");

  fileWatcher.onDidChange(async (uri) => {
    if (fileSync.isAutoSyncEnabled()) {
      await fileSync.syncFile(uri);
    }
  });

  fileWatcher.onDidCreate(async (uri) => {
    if (fileSync.isAutoSyncEnabled()) {
      await fileSync.syncFile(uri);
    }
  });

  fileWatcher.onDidDelete(async (uri) => {
    if (fileSync.isAutoSyncEnabled()) {
      await fileSync.deleteRemoteFile(uri);
    }
  });

  context.subscriptions.push(fileWatcher);
}

// Extension deactivation
export function deactivate() {
  console.log("GCP IDE Sync extension is now deactivated");
}
