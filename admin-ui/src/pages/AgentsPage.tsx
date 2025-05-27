import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator'; // Corrected path
import { MoreHorizontal, Edit, Trash2, Eye, PlusCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from '@tanstack/react-router'; // For "Create Agent" button link

// Mock Data
const mockAgents = [
  { id: 'agt_001', name: 'Content Writer Pro', status: 'active', lastUpdated: '2024-07-29 10:00 AM', version: '1.2.3' },
  { id: 'agt_002', name: 'Data Analyst Bot X', status: 'idle', lastUpdated: '2024-07-28 15:30 PM', version: '2.0.1' },
  { id: 'agt_003', name: 'Customer Support AI v2', status: 'error', lastUpdated: '2024-07-29 09:00 AM', version: '0.9.5' },
  { id: 'agt_004', name: 'Image Generation Unit', status: 'active', lastUpdated: '2024-07-29 11:15 AM', version: '1.5.0' },
  { id: 'agt_005', name: 'Code Assistant Beta', status: 'offline', lastUpdated: '2024-07-27 18:00 PM', version: '0.7.2' },
  { id: 'agt_006', name: 'Research Aggregator', status: 'active', lastUpdated: '2024-07-29 14:20 PM', version: '3.1.0' },
  { id: 'agt_007', name: 'Translation Service', status: 'idle', lastUpdated: '2024-07-29 08:30 AM', version: '1.0.0' },
];

export function AgentsPage() {
  // Placeholder for handling actions - in a real app, these would trigger API calls or navigation
  const handleAction = (action: string, agentId: string) => {
    alert(`${action} action triggered for agent ${agentId}`);
    console.log(`${action} action for agent ${agentId}`);
  };

  return (
    <PageWrapper title="Agents Management">
      <div className="flex items-center justify-between mb-6">
        <p className="text-muted-foreground">
          Monitor, manage, and configure your AI agents.
        </p>
        <Button asChild>
          <Link to="/agents/new"> {/* Assuming a route for creating new agents */}
            <PlusCircle className="mr-2 h-4 w-4" /> Create Agent
          </Link>
        </Button>
      </div>

      {/* Using a Card component to wrap the table for consistent styling */}
      <div className="bg-card p-0 border rounded-lg shadow-sm"> {/* p-0 to allow table to span full width of card */}
        <div className="overflow-x-auto"> {/* For responsiveness on smaller screens */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Agent ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Version</TableHead>
                <TableHead>Last Updated</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockAgents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell className="font-mono text-xs">{agent.id}</TableCell>
                  <TableCell className="font-medium">{agent.name}</TableCell>
                  <TableCell>
                    <StatusIndicator status={agent.status} />
                  </TableCell>
                  <TableCell>{agent.version}</TableCell>
                  <TableCell>{agent.lastUpdated}</TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleAction('View Details', agent.id)}>
                          <Eye className="mr-2 h-4 w-4" /> View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Edit', agent.id)}>
                          <Edit className="mr-2 h-4 w-4" /> Edit Agent
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={() => handleAction('Delete', agent.id)}
                          className="text-red-500 hover:!text-red-600 focus:text-red-600"
                        >
                          <Trash2 className="mr-2 h-4 w-4" /> Delete Agent
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
      {/* TODO: Implement pagination if agent list grows */}
    </PageWrapper>
  );
}
