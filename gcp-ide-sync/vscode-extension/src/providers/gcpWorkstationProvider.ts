import * as vscode from "vscode";
import { GcpAuthManager } from "../auth/gcpAuthManager";

/**
 * Tree item representing a GCP workstation
 */
class WorkstationTreeItem extends vscode.TreeItem {
  constructor(
    public readonly id: string,
    public readonly label: string,
    public readonly state: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
  ) {
    super(label, collapsibleState);

    // Set context value based on state
    this.contextValue =
      state === "RUNNING" ? "workstation-running" : "workstation-stopped";

    // Set icon based on state
    this.iconPath =
      state === "RUNNING"
        ? new vscode.ThemeIcon("vm-running")
        : new vscode.ThemeIcon("vm-outline");

    // Set description to show state
    this.description = state;

    // Set tooltip
    this.tooltip = `Workstation: ${label}\nState: ${state}\nID: ${id}`;
  }
}

/**
 * Tree data provider for GCP workstations
 */
export class GcpWorkstationProvider
  implements vscode.TreeDataProvider<WorkstationTreeItem>
{
  private _onDidChangeTreeData: vscode.EventEmitter<
    WorkstationTreeItem | undefined | null | void
  > = new vscode.EventEmitter<WorkstationTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    WorkstationTreeItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private context: vscode.ExtensionContext;
  private authManager: GcpAuthManager;
  private refreshInterval: NodeJS.Timeout | null = null;

  constructor(context: vscode.ExtensionContext, authManager: GcpAuthManager) {
    this.context = context;
    this.authManager = authManager;

    // Start refresh interval
    this.startRefreshInterval();

    // Register commands
    context.subscriptions.push(
      vscode.commands.registerCommand("gcp-ide-sync.refreshWorkstations", () =>
        this.refresh(),
      ),
    );
  }

  /**
   * Start refresh interval
   */
  private startRefreshInterval(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    // Refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.refresh();
    }, 30000);
  }

  /**
   * Refresh the tree view
   */
  public refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  /**
   * Get tree item for a given element
   * @param element Tree item
   * @returns Tree item
   */
  getTreeItem(element: WorkstationTreeItem): vscode.TreeItem {
    return element;
  }

  /**
   * Get children of a tree item
   * @param element Parent tree item
   * @returns Array of child tree items
   */
  async getChildren(
    element?: WorkstationTreeItem,
  ): Promise<WorkstationTreeItem[]> {
    if (element) {
      // No children for workstation items
      return [];
    }

    try {
      // Check if authenticated
      if (!this.authManager.isAuthenticated()) {
        return [
          new WorkstationTreeItem(
            "not-authenticated",
            "Not authenticated",
            "ERROR",
            vscode.TreeItemCollapsibleState.None,
          ),
        ];
      }

      // Get workstations
      const workstations = await this.authManager.listWorkstations();

      if (workstations.length === 0) {
        return [
          new WorkstationTreeItem(
            "no-workstations",
            "No workstations found",
            "INFO",
            vscode.TreeItemCollapsibleState.None,
          ),
        ];
      }

      // Create tree items for workstations
      return workstations.map((ws) => {
        return new WorkstationTreeItem(
          ws.id,
          ws.name,
          ws.state,
          vscode.TreeItemCollapsibleState.None,
        );
      });
    } catch (error) {
      return [
        new WorkstationTreeItem(
          "error",
          `Error: ${error}`,
          "ERROR",
          vscode.TreeItemCollapsibleState.None,
        ),
      ];
    }
  }

  /**
   * Start a workstation
   * @param workstationId Workstation ID
   * @returns Promise<boolean> True if successful
   */
  public async startWorkstation(workstationId: string): Promise<boolean> {
    try {
      await this.authManager.startWorkstation(workstationId);
      this.refresh();
      return true;
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to start workstation: ${error}`);
      return false;
    }
  }

  /**
   * Stop a workstation
   * @param workstationId Workstation ID
   * @returns Promise<boolean> True if successful
   */
  public async stopWorkstation(workstationId: string): Promise<boolean> {
    try {
      await this.authManager.stopWorkstation(workstationId);
      this.refresh();
      return true;
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to stop workstation: ${error}`);
      return false;
    }
  }
}
