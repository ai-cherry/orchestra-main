import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { mcpApiService, UserDefinedMCPServerInstanceConfig } from '@/services/mcpApiService'; // Adjust path if needed

interface McpServerListProps {
    onEditServer: (server: UserDefinedMCPServerInstanceConfig) => void;
    onAddServer: () => void;
}

const McpServerList: React.FC<McpServerListProps> = ({ onEditServer, onAddServer }) => {
    const queryClient = useQueryClient();

    const { data: servers, isLoading, isError, error } = useQuery<UserDefinedMCPServerInstanceConfig[], Error>({
        queryKey: ['mcpServers'],
        queryFn: mcpApiService.getMcpServers,
    });

    const deleteMutation = useMutation({
        mutationFn: mcpApiService.deleteMcpServer,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['mcpServers'] });
            // TODO: Add toast notification for success
        },
        onError: (error: Error) => {
            // TODO: Add toast notification for error
            console.error("Failed to delete server:", error.message);
        },
    });

    const handleDelete = (serverId: string) => {
        if (window.confirm('Are you sure you want to delete this MCP server instance?')) {
            deleteMutation.mutate(serverId);
        }
    };

    if (isLoading) return <div className="p-4 text-center">Loading MCP server instances...</div>;
    if (isError) return <div className="p-4 text-center text-red-500">Error loading MCP servers: {error?.message}</div>;

    return (
        <div className="p-4 sm:p-6 lg:p-8">
            <div className="sm:flex sm:items-center">
                <div className="sm:flex-auto">
                    <h1 className="text-base font-semibold leading-6 text-gray-900">MCP Server Instances</h1>
                    <p className="mt-2 text-sm text-gray-700">
                        A list of all configured MCP (Multi-Purpose Copilot) server instances.
                    </p>
                </div>
                <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
                    <button
                        type="button"
                        onClick={onAddServer}
                        className="block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    >
                        Add New MCP Server
                    </button>
                </div>
            </div>
                <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                    <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                        {servers && servers.length > 0 ? (
                            <table className="min-w-full divide-y divide-gray-300">
                                <thead>
                                    <tr>
                                        <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">Name</th>
                                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Description</th>
                                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Target AI Coders</th>
                                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Desired Status</th>
                                        <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-0"><span className="sr-only">Actions</span></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 bg-white">
                                    {servers.map((server) => (
                                        <tr key={server.id}>
                                            <td className="whitespace-nowrap py-5 pl-4 pr-3 text-sm sm:pl-0">
                                                <div className="font-medium text-gray-900">{server.name}</div>
                                                <div className="mt-1 text-gray-500 text-xs italic">{server.id}</div>
                                            </td>
                                            <td className="whitespace-normal px-3 py-5 text-sm text-gray-500 max-w-xs truncate">
                                                {server.description || 'N/A'}
                                            </td>
                                            <td className="whitespace-nowrap px-3 py-5 text-sm text-gray-500">
                                                {server.target_ai_coders.join(', ')}
                                            </td>
                                            <td className="whitespace-nowrap px-3 py-5 text-sm text-gray-500">
                                                <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                                                    server.desired_status === 'running' ? 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20'
                                                                                       : 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20'
                                                }`}>
                                                    {server.desired_status}
                                                </span>
                                            </td>
                                            <td className="relative whitespace-nowrap py-5 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                                                <button onClick={() => onEditServer(server)} className="text-indigo-600 hover:text-indigo-900">
                                                    Edit<span className="sr-only">, {server.name}</span>
                                                </button>
                                                <button onClick={() => handleDelete(server.id)} className="ml-4 text-red-600 hover:text-red-900">
                                                    Delete<span className="sr-only">, {server.name}</span>
                                                </button>
                                                {/* TODO: Add View Status button later */}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="text-center py-10">
                                <p className="text-gray-500">No MCP server instances found.</p>
                                <p className="mt-2">
                                    <button
                                        type="button"
                                        onClick={onAddServer}
                                        className="text-sm font-semibold text-indigo-600 hover:text-indigo-500"
                                    >
                                        Create the first one
                                    </button>
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default McpServerList;
