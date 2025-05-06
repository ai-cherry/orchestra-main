import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as ssh2 from 'ssh2';
import { GcpAuthManager } from '../auth/gcpAuthManager';

/**
 * Manages terminal sessions with GCP workstations
 */
export class TerminalManager {
  private context: vscode.ExtensionContext;
  private authManager: GcpAuthManager;
  private terminals: Map<string, vscode.Terminal> = new Map();
  private sshConnections: Map<string, ssh2.Client> = new Map();
  
  constructor(context: vscode.ExtensionContext, authManager: GcpAuthManager) {
    this.context = context;
    this.authManager = authManager;
    
    // Register terminal close event
    context.subscriptions.push(
      vscode.window.onDidCloseTerminal(terminal => {
        this.handleTerminalClose(terminal);
      })
    );
  }
  
  /**
   * Open a terminal connected to the remote workstation
   * @returns Promise<vscode.Terminal> The created terminal
   */
  public async openTerminal(): Promise<vscode.Terminal> {
    try {
      if (!this.authManager.isAuthenticated()) {
        throw new Error('Not authenticated. Call authenticate() first.');
      }
      
      // Get workstations
      const workstations = await this.authManager.listWorkstations();
      
      if (workstations.length === 0) {
        throw new Error('No workstations found');
      }
      
      // If multiple workstations, prompt user to select one
      let selectedWorkstation;
      if (workstations.length === 1) {
        selectedWorkstation = workstations[0];
      } else {
        const workstationNames = workstations.map(ws => ws.name);
        const selected = await vscode.window.showQuickPick(workstationNames, {
          placeHolder: 'Select a workstation'
        });
        
        if (!selected) {
          throw new Error('No workstation selected');
        }
        
        selectedWorkstation = workstations.find(ws => ws.name === selected);
      }
      
      // Check if workstation is running
      if (selectedWorkstation.state !== 'RUNNING') {
        // Prompt user to start workstation
        const start = await vscode.window.showInformationMessage(
          `Workstation ${selectedWorkstation.name} is not running. Start it now?`,
          'Yes', 'No'
        );
        
        if (start !== 'Yes') {
          throw new Error('Workstation is not running');
        }
        
        // Start workstation
        await this.authManager.startWorkstation(selectedWorkstation.id);
        
        // Wait for workstation to start
        await vscode.window.withProgress({
          location: vscode.ProgressLocation.Notification,
          title: `Starting workstation ${selectedWorkstation.name}`,
          cancellable: false
        }, async (progress) => {
          let isRunning = false;
          while (!isRunning) {
            // Check workstation status
            const workstations = await this.authManager.listWorkstations();
            const updatedWorkstation = workstations.find(ws => ws.id === selectedWorkstation.id);
            
            if (updatedWorkstation && updatedWorkstation.state === 'RUNNING') {
              isRunning = true;
            } else {
              // Wait 5 seconds before checking again
              await new Promise(resolve => setTimeout(resolve, 5000));
            }
          }
        });
      }
      
      // Create SSH connection
      const sshClient = await this.createSshConnection(selectedWorkstation);
      
      // Create terminal
      const terminal = vscode.window.createTerminal({
        name: `GCP: ${selectedWorkstation.name}`,
        pty: {
          onDidWrite: (data: string) => {
            // Terminal output handling
          },
          onDidClose: () => {
            // Close SSH connection
            if (sshClient) {
              sshClient.end();
            }
          },
          open: () => {
            // Terminal opened
          },
          close: () => {
            // Terminal closed
          },
          handleInput: (data: string) => {
            // Send input to SSH connection
            if (sshClient && sshClient.stdin) {
              sshClient.stdin.write(data);
            }
          }
        }
      });
      
      // Store terminal and SSH connection
      this.terminals.set(selectedWorkstation.id, terminal);
      this.sshConnections.set(selectedWorkstation.id, sshClient);
      
      // Show terminal
      terminal.show();
      
      return terminal;
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to open terminal: ${error}`);
      throw error;
    }
  }
  
  /**
   * Create an SSH connection to the workstation
   * @param workstation Workstation to connect to
   * @returns Promise<ssh2.Client> SSH client
   */
  private async createSshConnection(workstation: any): Promise<ssh2.Client> {
    return new Promise((resolve, reject) => {
      try {
        // Get SSH key
        const sshKeyPath = path.join(this.context.globalStorageUri.fsPath, 'ssh_key');
        
        // Check if SSH key exists
        if (!fs.existsSync(sshKeyPath)) {
          // Generate SSH key
          // This is a simplified example - in a real implementation, you would generate a proper SSH key
          fs.writeFileSync(sshKeyPath, 'DUMMY_SSH_KEY');
          fs.chmodSync(sshKeyPath, 0o600);
        }
        
        // Create SSH client
        const client = new ssh2.Client();
        
        client.on('ready', () => {
          client.shell((err, stream) => {
            if (err) {
              reject(err);
              return;
            }
            
            // Handle stream events
            stream.on('data', (data: Buffer) => {
              // Process terminal output
            });
            
            stream.on('close', () => {
              client.end();
            });
            
            // Store stream for input
            client.stdin = stream;
            
            resolve(client);
          });
        });
        
        client.on('error', (err) => {
          reject(err);
        });
        
        // Connect to workstation
        client.connect({
          host: workstation.host || 'localhost',
          port: workstation.port || 22,
          username: workstation.username || 'user',
          privateKey: fs.readFileSync(sshKeyPath)
        });
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Handle terminal close event
   * @param terminal Terminal that was closed
   */
  private handleTerminalClose(terminal: vscode.Terminal): void {
    // Find workstation ID for terminal
    let workstationId: string | undefined;
    
    for (const [id, term] of this.terminals.entries()) {
      if (term === terminal) {
        workstationId = id;
        break;
      }
    }
    
    if (workstationId) {
      // Close SSH connection
      const sshClient = this.sshConnections.get(workstationId);
      if (sshClient) {
        sshClient.end();
        this.sshConnections.delete(workstationId);
      }
      
      // Remove terminal from map
      this.terminals.delete(workstationId);
    }
  }
  
  /**
   * Close all terminals
   */
  public async closeAllTerminals(): Promise<void> {
    // Close all SSH connections
    for (const client of this.sshConnections.values()) {
      client.end();
    }
    
    // Clear maps
    this.sshConnections.clear();
    this.terminals.clear();
    
    // Close all terminals
    vscode.window.terminals.forEach(terminal => {
      if (terminal.name.startsWith('GCP:')) {
        terminal.dispose();
      }
    });
  }
}