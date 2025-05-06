import * as vscode from 'vscode';

/**
 * Manages the status bar UI for the extension
 */
export class StatusBarManager {
  private context: vscode.ExtensionContext;
  private statusBarItem: vscode.StatusBarItem;
  private syncingStatusBarItem: vscode.StatusBarItem | undefined;
  
  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    
    // Create status bar item
    this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    this.statusBarItem.command = 'gcp-ide-sync.connect';
    this.setDisconnected();
    this.statusBarItem.show();
    
    // Add to subscriptions
    context.subscriptions.push(this.statusBarItem);
  }
  
  /**
   * Set status bar to connected state
   */
  public setConnected(): void {
    this.statusBarItem.text = '$(cloud) GCP: Connected';
    this.statusBarItem.tooltip = 'Connected to GCP Workstation';
    this.statusBarItem.command = 'gcp-ide-sync.disconnect';
  }
  
  /**
   * Set status bar to disconnected state
   */
  public setDisconnected(): void {
    this.statusBarItem.text = '$(cloud) GCP: Disconnected';
    this.statusBarItem.tooltip = 'Connect to GCP Workstation';
    this.statusBarItem.command = 'gcp-ide-sync.connect';
  }
  
  /**
   * Show syncing indicator
   */
  public showSyncing(): void {
    if (!this.syncingStatusBarItem) {
      this.syncingStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
      this.context.subscriptions.push(this.syncingStatusBarItem);
    }
    
    this.syncingStatusBarItem.text = '$(sync) Syncing...';
    this.syncingStatusBarItem.tooltip = 'Syncing files with GCP Workstation';
    this.syncingStatusBarItem.show();
  }
  
  /**
   * Hide syncing indicator
   */
  public hideSyncing(): void {
    if (this.syncingStatusBarItem) {
      this.syncingStatusBarItem.hide();
    }
  }
  
  /**
   * Show error in status bar
   * @param message Error message
   */
  public showError(message: string): void {
    this.statusBarItem.text = '$(error) GCP: Error';
    this.statusBarItem.tooltip = message;
    
    // Reset after 5 seconds
    setTimeout(() => {
      this.setDisconnected();
    }, 5000);
  }
}