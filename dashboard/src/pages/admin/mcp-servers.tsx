import React, { useState } from 'react';
import Head from 'next/head';
import McpServerList from '@/components/mcp/McpServerList'; // Adjust path if needed
import McpServerForm from '@/components/mcp/McpServerForm'; // Adjust path if needed
import { UserDefinedMCPServerInstanceConfig } from '@/services/mcpApiService'; // Adjust path if needed
import { useQueryClient } from '@tanstack/react-query'; // For potential optimistic updates or fine-grained cache control

// Basic Modal Component (can be replaced with a more sophisticated one from a library)
interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-end justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
                {/* Background overlay */}
                <div className="fixed inset-0 transition-opacity" aria-hidden="true" onClick={onClose}>
                    <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>

                {/* This element is to trick the browser into centering the modal contents. */}
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                {/* Modal panel */}
                <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                    <div>
                        <h3 className="text-lg font-medium leading-6 text-gray-900" id="modal-title">
                            {title}
                        </h3>
                        <div className="mt-2">
                            {children}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};


const McpServersAdminPage: React.FC = () => {
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingServer, setEditingServer] = useState<UserDefinedMCPServerInstanceConfig | null>(null);
    const queryClient = useQueryClient(); // Useful if direct cache manipulation is needed beyond invalidation

    const handleAddServer = () => {
        setEditingServer(null);
        setIsFormOpen(true);
    };

    const handleEditServer = (server: UserDefinedMCPServerInstanceConfig) => {
        setEditingServer(server);
        setIsFormOpen(true);
    };

    const handleFormSave = (savedServer: UserDefinedMCPServerInstanceConfig) => {
        // Invalidation is handled by the form's mutation, but could also be done here.
        // queryClient.invalidateQueries(['mcpServers']);
        setIsFormOpen(false);
        setEditingServer(null);
        // Potentially show a success notification here
    };

    const handleFormCancel = () => {
        setIsFormOpen(false);
        setEditingServer(null);
    };

    return (
        <>
            <Head>
                <title>MCP Server Management | Admin Dashboard</title>
            </Head>
            <div className="min-h-screen bg-gray-100"> {/* Optional: background for the page */}
                <header className="bg-white shadow-sm">
                    <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
                        <h1 className="text-lg font-semibold leading-6 text-gray-900">
                            Admin Dashboard
                        </h1>
                    </div>
                </header>
                <main className="mx-auto max-w-7xl py-6 sm:px-6 lg:px-8">
                    <McpServerList
                        onAddServer={handleAddServer}
                        onEditServer={handleEditServer}
                    />
                    <Modal
                        isOpen={isFormOpen}
                        onClose={handleFormCancel}
                        title={editingServer ? 'Edit MCP Server Instance' : 'Add New MCP Server Instance'}
                    >
                        <McpServerForm
                            initialData={editingServer}
                            onSave={handleFormSave}
                            onCancel={handleFormCancel}
                            // isLoading prop could be passed if mutations were handled here instead of inside McpServerForm
                        />
                    </Modal>
                </main>
            </div>
        </>
    );
};

export default McpServersAdminPage;

// Note: This page assumes Pages Router.
// For App Router, this would be a `page.tsx` file inside an `admin/mcp-servers` directory,
// and layout would be handled by `layout.tsx`.
// The Modal is a basic implementation; a library like Headless UI would be more robust.
// Ensure @tanstack/react-query QueryClientProvider is set up in _app.tsx.
