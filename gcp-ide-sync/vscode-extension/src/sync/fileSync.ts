import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import axios from 'axios';
import { GcpAuthManager } from '../auth/gcpAuthManager';

/**
 * Handles file synchronization between local and remote environments
 */
export class FileSync {
  private context: vscode.ExtensionContext;
  private authManager: GcpAuthManager;
  private syncInProgress: boolean = false;
  private syncQueue: vscode.Uri[] = [];
  private deleteQueue: vscode.Uri[] = [];
  private syncInterval: NodeJS.Timeout | null = null;
  private remoteBasePath: string = '/home/user/mounted_repos';
  private localBasePath: string = '';
  
  constructor(context: vscode.ExtensionContext, authManager: GcpAuthManager) {
    this.context = context;
    this.authManager = authManager;
    this.loadConfig();
  }
  
  /**
   * Load configuration from VS Code settings
   */
  private loadConfig(): void {
    const config = vscode.workspace.getConfiguration('gcp-ide-sync');
    const workspaceFolders = vscode.workspace.workspaceFolders;
    
    if (workspaceFolders && workspaceFolders.length > 0) {
      this.localBasePath = workspaceFolders[0].uri.fsPath;
    }
  }
  
  /**
   * Check if auto sync is enabled
   * @returns boolean True if auto sync is enabled
   */
  public isAutoSyncEnabled(): boolean {
    const config = vscode.workspace.getConfiguration('gcp-ide-sync');
    return config.get<boolean>('autoSync') || false;
  }
  
  /**
   * Perform initial synchronization of all files
   * @returns Promise<void>
   */
  public async initialSync(): Promise<void> {
    try {
      if (!this.authManager.isAuthenticated()) {
        throw new Error('Not authenticated. Call authenticate() first.');
      }
      
      vscode.window.showInformationMessage('Starting initial file synchronization...');
      
      // Get all files in the workspace
      const files = await vscode.workspace.findFiles('**/*', '**/node_modules/**');
      
      // Create progress notification
      vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Synchronizing files',
        cancellable: true
      }, async (progress, token) => {
        // Calculate total files
        const totalFiles = files.length;
        let syncedFiles = 0;
        
        // Process each file
        for (const file of files) {
          if (token.isCancellationRequested) {
            break;
          }
          
          try {
            // Skip directories
            const stat = fs.statSync(file.fsPath);
            if (stat.isDirectory()) {
              continue;
            }
            
            // Sync file
            await this.syncFile(file);
            
            // Update progress
            syncedFiles++;
            progress.report({
              message: `${syncedFiles}/${totalFiles} files`,
              increment: (1 / totalFiles) * 100
            });
          } catch (error) {
            console.error(`Error syncing file ${file.fsPath}:`, error);
          }
        }
        
        vscode.window.showInformationMessage(`Initial sync complete. Synchronized ${syncedFiles} files.`);
      });
      
      // Start auto sync if enabled
      if (this.isAutoSyncEnabled()) {
        this.startAutoSync();
      }
    } catch (error) {
      vscode.window.showErrorMessage(`Initial sync failed: ${error}`);
    }
  }
  
  /**
   * Start automatic synchronization
   */
  private startAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    
    const config = vscode.workspace.getConfiguration('gcp-ide-sync');
    const interval = config.get<number>('syncInterval') || 5000;
    
    this.syncInterval = setInterval(() => {
      this.processSyncQueue();
    }, interval);
  }
  
  /**
   * Stop automatic synchronization
   */
  public async stopSync(): Promise<void> {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }
  
  /**
   * Process the sync queue
   */
  private async processSyncQueue(): Promise<void> {
    if (this.syncInProgress || this.syncQueue.length === 0) {
      return;
    }
    
    this.syncInProgress = true;
    
    try {
      // Process file sync queue
      while (this.syncQueue.length > 0) {
        const uri = this.syncQueue.shift();
        if (uri) {
          await this.syncFileToRemote(uri);
        }
      }
      
      // Process file delete queue
      while (this.deleteQueue.length > 0) {
        const uri = this.deleteQueue.shift();
        if (uri) {
          await this.deleteRemoteFile(uri);
        }
      }
    } catch (error) {
      console.error('Error processing sync queue:', error);
    } finally {
      this.syncInProgress = false;
    }
  }
  
  /**
   * Sync a file to the remote environment
   * @param uri File URI
   * @returns Promise<void>
   */
  public async syncFile(uri: vscode.Uri): Promise<void> {
    // Add to sync queue
    if (!this.syncQueue.some(item => item.fsPath === uri.fsPath)) {
      this.syncQueue.push(uri);
    }
    
    // Process queue immediately if not in auto sync mode
    if (!this.isAutoSyncEnabled() || !this.syncInterval) {
      await this.processSyncQueue();
    }
  }
  
  /**
   * Delete a file from the remote environment
   * @param uri File URI
   * @returns Promise<void>
   */
  public async deleteRemoteFile(uri: vscode.Uri): Promise<void> {
    // Add to delete queue
    if (!this.deleteQueue.some(item => item.fsPath === uri.fsPath)) {
      this.deleteQueue.push(uri);
    }
    
    // Process queue immediately if not in auto sync mode
    if (!this.isAutoSyncEnabled() || !this.syncInterval) {
      await this.processSyncQueue();
    }
  }
  
  /**
   * Perform manual synchronization
   * @returns Promise<void>
   */
  public async manualSync(): Promise<void> {
    await this.initialSync();
  }
  
  /**
   * Sync a file to the remote environment
   * @param uri File URI
   * @returns Promise<void>
   */
  private async syncFileToRemote(uri: vscode.Uri): Promise<void> {
    try {
      if (!this.authManager.isAuthenticated()) {
        throw new Error('Not authenticated. Call authenticate() first.');
      }
      
      // Get relative path
      const relativePath = path.relative(this.localBasePath, uri.fsPath);
      const remoteFilePath = path.join(this.remoteBasePath, relativePath).replace(/\\/g, '/');
      
      // Read file content
      const content = fs.readFileSync(uri.fsPath);
      
      // Get authenticated client
      const client = await this.authManager.getAuthenticatedClient();
      
      // Create directory structure if needed
      const remoteDir = path.dirname(remoteFilePath);
      await client.post(`https://workstations.googleapis.com/v1/projects/${this.authManager.getProjectId()}/locations/${this.authManager.getRegion()}/workstations/execute`, {
        command: `mkdir -p "${remoteDir}"`
      });
      
      // Upload file
      await client.post(`https://workstations.googleapis.com/v1/projects/${this.authManager.getProjectId()}/locations/${this.authManager.getRegion()}/workstations/execute`, {
        command: `cat > "${remoteFilePath}"`,
        stdin: content.toString('base64')
      });
    } catch (error) {
      console.error(`Error syncing file ${uri.fsPath}:`, error);
    }
  }
}
