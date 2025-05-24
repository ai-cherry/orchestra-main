import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { GoogleAuth, JWT } from "google-auth-library";
import axios from "axios";

/**
 * Manages authentication with Google Cloud Platform
 */
export class GcpAuthManager {
  private context: vscode.ExtensionContext;
  private client: JWT | null = null;
  private projectId: string = "";
  private region: string = "";

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.loadConfig();
  }

  /**
   * Load configuration from VS Code settings
   */
  private loadConfig(): void {
    const config = vscode.workspace.getConfiguration("gcp-ide-sync");
    this.projectId = config.get<string>("projectId") || "";
    this.region = config.get<string>("region") || "";
  }

  /**
   * Authenticate with GCP using service account key
   * @returns Promise<boolean> True if authentication was successful
   */
  public async authenticate(): Promise<boolean> {
    try {
      // Get service account key path from settings
      const config = vscode.workspace.getConfiguration("gcp-ide-sync");
      const keyPath = config.get<string>("serviceAccountKeyPath") || "";

      if (!keyPath) {
        // If no key path is provided, prompt user to select key file
        const keyFile = await vscode.window.showOpenDialog({
          canSelectFiles: true,
          canSelectFolders: false,
          canSelectMany: false,
          filters: {
            JSON: ["json"],
          },
          title: "Select GCP Service Account Key File",
        });

        if (!keyFile || keyFile.length === 0) {
          vscode.window.showErrorMessage(
            "No service account key file selected",
          );
          return false;
        }

        // Save the selected key path to settings
        await config.update(
          "serviceAccountKeyPath",
          keyFile[0].fsPath,
          vscode.ConfigurationTarget.Global,
        );

        // Load the key file
        const keyContent = fs.readFileSync(keyFile[0].fsPath, "utf8");
        const key = JSON.parse(keyContent);

        // Create JWT client
        this.client = new JWT({
          email: key.client_email,
          key: key.private_key,
          scopes: [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/compute",
          ],
        });

        // Set project ID if not already set
        if (!this.projectId) {
          this.projectId = key.project_id;
          await config.update(
            "projectId",
            this.projectId,
            vscode.ConfigurationTarget.Global,
          );
        }
      } else {
        // Load the key file from the saved path
        const keyContent = fs.readFileSync(keyPath, "utf8");
        const key = JSON.parse(keyContent);

        // Create JWT client
        this.client = new JWT({
          email: key.client_email,
          key: key.private_key,
          scopes: [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/compute",
          ],
        });
      }

      // Test authentication by getting an access token
      await this.client.getAccessToken();

      vscode.window.showInformationMessage(
        "Successfully authenticated with GCP",
      );
      return true;
    } catch (error) {
      vscode.window.showErrorMessage(`Authentication failed: ${error}`);
      return false;
    }
  }

  /**
   * Get an authenticated axios instance for making API requests
   * @returns Promise<axios.AxiosInstance> Authenticated axios instance
   */
  public async getAuthenticatedClient(): Promise<axios.AxiosInstance> {
    if (!this.client) {
      throw new Error("Not authenticated. Call authenticate() first.");
    }

    const token = await this.client.getAccessToken();

    return axios.create({
      headers: {
        Authorization: `Bearer ${token.token}`,
      },
    });
  }

  /**
   * Get the GCP project ID
   * @returns string Project ID
   */
  public getProjectId(): string {
    return this.projectId;
  }

  /**
   * Get the GCP region
   * @returns string Region
   */
  public getRegion(): string {
    return this.region;
  }

  /**
   * Check if authenticated
   * @returns boolean True if authenticated
   */
  public isAuthenticated(): boolean {
    return this.client !== null;
  }

  /**
   * List available workstations
   * @returns Promise<any[]> List of workstations
   */
  public async listWorkstations(): Promise<any[]> {
    try {
      if (!this.client) {
        throw new Error("Not authenticated. Call authenticate() first.");
      }

      const client = await this.getAuthenticatedClient();
      const response = await client.get(
        `https://workstations.googleapis.com/v1/projects/${this.projectId}/locations/${this.region}/workstations`,
      );

      return response.data.workstations || [];
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to list workstations: ${error}`);
      return [];
    }
  }

  /**
   * Start a workstation
   * @param workstationId Workstation ID
   * @returns Promise<boolean> True if successful
   */
  public async startWorkstation(workstationId: string): Promise<boolean> {
    try {
      if (!this.client) {
        throw new Error("Not authenticated. Call authenticate() first.");
      }

      const client = await this.getAuthenticatedClient();
      await client.post(
        `https://workstations.googleapis.com/v1/projects/${this.projectId}/locations/${this.region}/workstations/${workstationId}:start`,
      );

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
      if (!this.client) {
        throw new Error("Not authenticated. Call authenticate() first.");
      }

      const client = await this.getAuthenticatedClient();
      await client.post(
        `https://workstations.googleapis.com/v1/projects/${this.projectId}/locations/${this.region}/workstations/${workstationId}:stop`,
      );

      return true;
    } catch (error) {
      vscode.window.showErrorMessage(`Failed to stop workstation: ${error}`);
      return false;
    }
  }
}
