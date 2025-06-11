// MCP Server Management API Service

import { HttpUrl } from "pydantic"; // Assuming HttpUrl might be part of the shared models eventually
// However, for frontend, it's often just string. Let's use string for URL types for now.

// --- TypeScript Interfaces Mirroring Pydantic Models ---

// Literal types - Replicate these from Pydantic models if not already shared
// For simplicity, using string for now, but could be stricter with string literal unions.
type MCPTargetAICoder = "Coder" | "CursorAI" | "Claude" | "OpenAI_GPT4" | "OpenAI_GPT3_5" | "Gemini" | "Copilot" | "Generic";
type MCPEnabledInternalTool = "copilot" | "gemini";
type MCPDesiredStatus = "running" | "stopped";
type MCPAIProviderName = "openai" | "claude" | "gemini" | "copilot" | "custom";
type MCPContextSourceType = "git_repo" | "weaviate_collection" | "file_path" | "url_list";
type MCPServerActualStatus = "UNKNOWN" | "PENDING" | "PROVISIONING" | "RUNNING" | "STOPPED" | "STOPPING" | "ERROR" | "DELETING";


export interface MCPServerResourceConfig {
    cpu: string;
    memory: string;
    gpu_type?: string | null;
}

export interface AIProvider {
    name: MCPAIProviderName;
    api_key_secret_name?: string | null;
    model?: string | null;
}

export interface ContextSourceConfig {
    type: MCPContextSourceType;
    uri?: string | null;
    paths: string[];
    branch?: string | null;
}

export interface UserDefinedMCPServerInstanceConfig {
    id: string; // UUID as string
    name: string;
    description?: string | null;
    target_ai_coders: MCPTargetAICoder[];
    enabled_internal_tools: MCPEnabledInternalTool[];
    copilot_config_override?: Record<string, any> | null;
    gemini_config_override?: Record<string, any> | null;
    base_docker_image: string;
    resources: MCPServerResourceConfig;
    custom_environment_variables: Record<string, string>;
    ai_providers: AIProvider[];
    context_sources: ContextSourceConfig[];
    generated_mcp_internal_config_yaml?: string | null;
    desired_status: MCPDesiredStatus;
    created_at: string; // ISO datetime string
    updated_at: string; // ISO datetime string
}

// For creating a server, some fields are omitted or optional
export interface MCPServerCreateRequest {
    name: string;
    description?: string | null;
    target_ai_coders: MCPTargetAICoder[];
    enabled_internal_tools: MCPEnabledInternalTool[];
    copilot_config_override?: Record<string, any> | null;
    gemini_config_override?: Record<string, any> | null;
    base_docker_image?: string; // Optional at creation, server might have a default
    resources?: MCPServerResourceConfig;
    custom_environment_variables?: Record<string, string>;
    ai_providers?: AIProvider[];
    context_sources?: ContextSourceConfig[];
    desired_status?: MCPDesiredStatus;
}

// For updating, all fields that can be changed are optional
export type MCPServerUpdateRequest = Partial<Omit<MCPServerCreateRequest, 'name'>> & { name?: string };


export interface MCPServerInstanceStatus {
    instance_id: string; // UUID as string
    actual_status: MCPServerActualStatus;
    health_check_url?: string | null; // Assuming string for URL on frontend
    last_health_status?: string | null;
    last_status_check_at?: string | null; // ISO datetime string
    message?: string | null;
}

// --- API Service Implementation ---

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1/mcp";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail; // FastAPI often uses 'detail'
        } catch (e) {
            // Ignore if response is not JSON or already handled
        }
        throw new Error(errorDetail);
    }
    return response.json() as Promise<T>;
}

export const mcpApiService = {
    getMcpServers: async (): Promise<UserDefinedMCPServerInstanceConfig[]> => {
        const response = await fetch(`${API_BASE_URL}/servers`);
        return handleResponse<UserDefinedMCPServerInstanceConfig[]>(response);
    },

    getMcpServerById: async (serverId: string): Promise<UserDefinedMCPServerInstanceConfig> => {
        const response = await fetch(`${API_BASE_URL}/servers/${serverId}`);
        return handleResponse<UserDefinedMCPServerInstanceConfig>(response);
    },

    createMcpServer: async (data: MCPServerCreateRequest): Promise<UserDefinedMCPServerInstanceConfig> => {
        const response = await fetch(`${API_BASE_URL}/servers`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<UserDefinedMCPServerInstanceConfig>(response);
    },

    updateMcpServer: async (serverId: string, data: MCPServerUpdateRequest): Promise<UserDefinedMCPServerInstanceConfig> => {
        const response = await fetch(`${API_BASE_URL}/servers/${serverId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<UserDefinedMCPServerInstanceConfig>(response);
    },

    deleteMcpServer: async (serverId: string): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/servers/${serverId}`, {
            method: "DELETE",
        });
        if (!response.ok) { // For 204 No Content, response.json() would fail
            let errorDetail = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json(); // Attempt to get error detail if present
                errorDetail = errorData.detail || errorDetail;
            } catch (e) { /* ignore */ }
            throw new Error(errorDetail);
        }
        // No content to return for 204
    },

    getMcpServerStatus: async (serverId: string): Promise<MCPServerInstanceStatus> => {
        const response = await fetch(`${API_BASE_URL}/servers/${serverId}/status`);
        return handleResponse<MCPServerInstanceStatus>(response);
    },
};

// Example usage (for testing, can be removed)
// async function testApi() {
//     try {
//         console.log("Fetching servers...");
//         const servers = await mcpApiService.getMcpServers();
//         console.log("Servers:", servers);
//
//         if (servers.length > 0) {
//             const firstServerId = servers[0].id;
//             console.log(`Fetching server ${firstServerId}...`);
//             const server = await mcpApiService.getMcpServerById(firstServerId);
//             console.log("Server details:", server);
//
//             console.log(`Fetching status for server ${firstServerId}...`);
//             const status = await mcpApiService.getMcpServerStatus(firstServerId);
//             console.log("Server status:", status);
//         }
//     } catch (error) {
//         console.error("API Test Error:", error);
//     }
// }
// testApi();
