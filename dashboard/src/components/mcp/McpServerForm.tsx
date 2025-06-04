import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
    mcpApiService,
    UserDefinedMCPServerInstanceConfig,
    MCPServerCreateRequest,
    MCPServerUpdateRequest,
    MCPServerResourceConfig,
    AIProvider,
    ContextSourceConfig
} from '@/services/mcpApiService'; // Adjust path as needed

// Define literals for form options (should match those in mcpApiService.ts)
const TARGET_AI_CODERS = ["RooCoder", "CursorAI", "Claude", "OpenAI_GPT4", "OpenAI_GPT3_5", "Gemini", "Copilot", "Generic"] as const;
const ENABLED_INTERNAL_TOOLS = ["copilot", "gemini"] as const;
const DESIRED_STATUS_OPTIONS = ["running", "stopped"] as const;
const AI_PROVIDER_NAMES = ["openai", "claude", "gemini", "copilot", "custom"] as const;
const CONTEXT_SOURCE_TYPES = ["git_repo", "weaviate_collection", "file_path", "url_list"] as const;


type FormData = Omit<MCPServerCreateRequest,
    'resources' |
    'custom_environment_variables' |
    'ai_providers' |
    'context_sources' |
    'copilot_config_override' |
    'gemini_config_override'
> & {
    resources_json: string;
    custom_environment_variables_json: string;
    ai_providers_json: string;
    context_sources_json: string;
    copilot_config_override_json: string;
    gemini_config_override_json: string;
};

interface McpServerFormProps {
    initialData?: UserDefinedMCPServerInstanceConfig | null;
    onSave: (data: UserDefinedMCPServerInstanceConfig) => void;
    onCancel: () => void;
    isLoading?: boolean; // To be controlled by parent for mutation status
}

const McpServerForm: React.FC<McpServerFormProps> = ({ initialData, onSave, onCancel, isLoading: parentIsLoading }) => {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState<FormData>({
        name: initialData?.name || '',
        description: initialData?.description || '',
        target_ai_coders: initialData?.target_ai_coders || [],
        enabled_internal_tools: initialData?.enabled_internal_tools || [],
        base_docker_image: initialData?.base_docker_image || 'mcp_server:latest',
        desired_status: initialData?.desired_status || 'running',
        // JSON text areas
        resources_json: JSON.stringify(initialData?.resources || { cpu: "1", memory: "2Gi" }, null, 2),
        custom_environment_variables_json: JSON.stringify(initialData?.custom_environment_variables || {}, null, 2),
        ai_providers_json: JSON.stringify(initialData?.ai_providers || [], null, 2),
        context_sources_json: JSON.stringify(initialData?.context_sources || [], null, 2),
        copilot_config_override_json: JSON.stringify(initialData?.copilot_config_override || {}, null, 2),
        gemini_config_override_json: JSON.stringify(initialData?.gemini_config_override || {}, null, 2),
    });
    const [formError, setFormError] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: (serverData: { id?: string; data: MCPServerCreateRequest | MCPServerUpdateRequest }) => {
            if (serverData.id) {
                return mcpApiService.updateMcpServer(serverData.id, serverData.data as MCPServerUpdateRequest);
            }
            return mcpApiService.createMcpServer(serverData.data as MCPServerCreateRequest);
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['mcpServers'] });
            onSave(data);
            // TODO: Add toast notification for success
        },
        onError: (error: Error) => {
            setFormError(error.message || "An unexpected error occurred.");
            // TODO: Add toast notification for error
        }
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleMultiSelectChange = (name: 'target_ai_coders' | 'enabled_internal_tools', value: string) => {
        setFormData(prev => {
            const currentSelection = prev[name] as string[];
            const newSelection = currentSelection.includes(value)
                ? currentSelection.filter(item => item !== value)
                : [...currentSelection, value];
            return { ...prev, [name]: newSelection };
        });
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setFormError(null);

        try {
            const resources: MCPServerResourceConfig = JSON.parse(formData.resources_json);
            const custom_environment_variables: Record<string, string> = JSON.parse(formData.custom_environment_variables_json);
            const ai_providers: AIProvider[] = JSON.parse(formData.ai_providers_json);
            const context_sources: ContextSourceConfig[] = JSON.parse(formData.context_sources_json);
            const copilot_config_override: Record<string, any> | undefined = formData.copilot_config_override_json.trim() ? JSON.parse(formData.copilot_config_override_json) : undefined;
            const gemini_config_override: Record<string, any> | undefined = formData.gemini_config_override_json.trim() ? JSON.parse(formData.gemini_config_override_json) : undefined;

            const payload: MCPServerCreateRequest | MCPServerUpdateRequest = {
                name: formData.name,
                description: formData.description || null,
                target_ai_coders: formData.target_ai_coders,
                enabled_internal_tools: formData.enabled_internal_tools,
                base_docker_image: formData.base_docker_image,
                desired_status: formData.desired_status,
                resources,
                custom_environment_variables,
                ai_providers,
                context_sources,
                copilot_config_override: copilot_config_override || null,
                gemini_config_override: gemini_config_override || null,
            };

            mutation.mutate({ id: initialData?.id, data: payload });

        } catch (jsonError: any) {
            setFormError(`Invalid JSON in one of the text areas: ${jsonError.message}`);
            return;
        }
    };

    const fieldsetStyle = "mb-6";
    const labelStyle = "block text-sm font-medium text-gray-700 mb-1";
    const inputStyle = "block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm";
    const textareaStyle = `${inputStyle} min-h-[100px] font-mono text-xs`;
    const checkboxLabelStyle = "ml-2 text-sm text-gray-700";

    return (
        <form onSubmit={handleSubmit} className="space-y-6 p-4 bg-white rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900">{initialData ? 'Edit' : 'Create'} MCP Server</h2>

            {formError && <div className="p-3 bg-red-50 text-red-700 rounded-md">{formError}</div>}

            <div className={fieldsetStyle}>
                <label htmlFor="name" className={labelStyle}>Name*</label>
                <input type="text" name="name" id="name" value={formData.name} onChange={handleChange} className={inputStyle} required />
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="description" className={labelStyle}>Description</label>
                <textarea name="description" id="description" value={formData.description} onChange={handleChange} className={textareaStyle} />
            </div>

            <div className={fieldsetStyle}>
                <label className={labelStyle}>Target AI Coders*</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {TARGET_AI_CODERS.map(coder => (
                        <div key={coder} className="flex items-center">
                            <input
                                type="checkbox" id={`coder-${coder}`} name="target_ai_coders" value={coder}
                                checked={formData.target_ai_coders.includes(coder)}
                                onChange={() => handleMultiSelectChange('target_ai_coders', coder)}
                                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                            />
                            <label htmlFor={`coder-${coder}`} className={checkboxLabelStyle}>{coder}</label>
                        </div>
                    ))}
                </div>
                {formData.target_ai_coders.length === 0 && <p className="text-xs text-red-500 mt-1">At least one AI Coder must be selected.</p>}
            </div>

            <div className={fieldsetStyle}>
                <label className={labelStyle}>Enabled Internal Tools</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                     {ENABLED_INTERNAL_TOOLS.map(tool => (
                        <div key={tool} className="flex items-center">
                            <input
                                type="checkbox" id={`tool-${tool}`} name="enabled_internal_tools" value={tool}
                                checked={formData.enabled_internal_tools.includes(tool)}
                                onChange={() => handleMultiSelectChange('enabled_internal_tools', tool)}
                                className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                            />
                            <label htmlFor={`tool-${tool}`} className={checkboxLabelStyle}>{tool}</label>
                        </div>
                    ))}
                </div>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="base_docker_image" className={labelStyle}>Base Docker Image</label>
                <input type="text" name="base_docker_image" id="base_docker_image" value={formData.base_docker_image} onChange={handleChange} className={inputStyle} />
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="desired_status" className={labelStyle}>Desired Status</label>
                <select name="desired_status" id="desired_status" value={formData.desired_status} onChange={handleChange} className={inputStyle}>
                    {DESIRED_STATUS_OPTIONS.map(status => <option key={status} value={status}>{status}</option>)}
                </select>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="resources_json" className={labelStyle}>Resources (JSON)</label>
                <textarea name="resources_json" id="resources_json" value={formData.resources_json} onChange={handleChange} className={textareaStyle} />
                <p className="mt-1 text-xs text-gray-500">Example: {`{"cpu": "1", "memory": "2Gi", "gpu_type": "nvidia-a100"}`}</p>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="copilot_config_override_json" className={labelStyle}>Copilot Config Override (JSON)</label>
                <textarea name="copilot_config_override_json" id="copilot_config_override_json" value={formData.copilot_config_override_json} onChange={handleChange} className={textareaStyle} />
                 <p className="mt-1 text-xs text-gray-500">JSON object for 'copilot' section overrides in MCPConfig. `api_key` will be ignored.</p>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="gemini_config_override_json" className={labelStyle}>Gemini Config Override (JSON)</label>
                <textarea name="gemini_config_override_json" id="gemini_config_override_json" value={formData.gemini_config_override_json} onChange={handleChange} className={textareaStyle} />
                <p className="mt-1 text-xs text-gray-500">JSON object for 'gemini' section overrides in MCPConfig. `api_key` will be ignored.</p>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="custom_environment_variables_json" className={labelStyle}>Custom Environment Variables (JSON)</label>
                <textarea name="custom_environment_variables_json" id="custom_environment_variables_json" value={formData.custom_environment_variables_json} onChange={handleChange} className={textareaStyle} />
                <p className="mt-1 text-xs text-gray-500">Example: {`{"MY_VAR": "value", "ANOTHER_VAR": "othervalue"}`}</p>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="ai_providers_json" className={labelStyle}>AI Providers (JSON Array)</label>
                <textarea name="ai_providers_json" id="ai_providers_json" value={formData.ai_providers_json} onChange={handleChange} className={textareaStyle} />
                <p className="mt-1 text-xs text-gray-500">Example: {`[{"name": "openai", "api_key_secret_name": "MY_OPENAI_KEY_SECRET", "model": "gpt-4"}]`}</p>
            </div>

            <div className={fieldsetStyle}>
                <label htmlFor="context_sources_json" className={labelStyle}>Context Sources (JSON Array)</label>
                <textarea name="context_sources_json" id="context_sources_json" value={formData.context_sources_json} onChange={handleChange} className={textareaStyle} />
                <p className="mt-1 text-xs text-gray-500">Example: {`[{"type": "git_repo", "uri": "https://github.com/...", "branch": "main"}]`}</p>
            </div>

            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button type="button" onClick={onCancel} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50">
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={mutation.isPending || parentIsLoading || formData.target_ai_coders.length === 0}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md shadow-sm hover:bg-indigo-700 disabled:opacity-50"
                >
                    {mutation.isPending || parentIsLoading ? 'Saving...' : (initialData ? 'Save Changes' : 'Create Server')}
                </button>
            </div>
        </form>
    );
};

export default McpServerForm;
