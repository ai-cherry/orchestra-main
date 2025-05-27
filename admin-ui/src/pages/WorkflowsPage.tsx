import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator'; // Ensure this path is correct
import { MoreHorizontal, Edit, Trash2, Eye, Play, Pause, PlusCircle, Clock, Zap } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from '@tanstack/react-router'; // For "Create Workflow" button link

type WorkflowStatus = 'Active' | 'Paused' | 'Error';
type TriggerType = 'Scheduled' | 'Webhook' | 'Manual';

// Mock Data
const mockWorkflows = [
  { id: 'wf_001', name: 'Daily Content Summary', description: 'Generates a summary of new content from various sources every morning.', status: 'Active' as WorkflowStatus, lastRun: '2024-07-30 08:00:15 AM', triggerType: 'Scheduled' as TriggerType },
  { id: 'wf_002', name: 'New User Onboarding', description: 'Sends welcome email series and assigns initial tasks to new users upon signup.', status: 'Paused' as WorkflowStatus, lastRun: '2024-07-29 12:05:30 PM', triggerType: 'Webhook' as TriggerType },
  { id: 'wf_003', name: 'Data Sync with CRM', description: 'Nightly synchronization of customer data between internal DB and external CRM.', status: 'Error' as WorkflowStatus, lastRun: '2024-07-30 02:01:05 AM', triggerType: 'Scheduled' as TriggerType },
  { id: 'wf_004', name: 'Social Media Poster', description: 'Automatically posts approved content to social media channels based on a schedule.', status: 'Active' as WorkflowStatus, lastRun: '2024-07-30 11:30:00 AM', triggerType: 'Scheduled' as TriggerType },
  { id: 'wf_005', name: 'Invoice Generation', description: 'Generates and sends invoices to clients at the end of each month.', status: 'Active' as WorkflowStatus, lastRun: '2024-07-28 00:05:00 AM', triggerType: 'Scheduled' as TriggerType },
  { id: 'wf_006', name: 'Support Ticket Escalation', description: 'Escalates unresolved support tickets after 24 hours to the appropriate team.', status: 'Paused' as WorkflowStatus, lastRun: '2024-07-25 10:00:00 AM', triggerType: 'Manual' as TriggerType },
  { id: 'wf_007', name: 'Failed Payment Retry', description: 'Attempts to retry failed subscription payments three times over three days.', status: 'Active' as WorkflowStatus, lastRun: '2024-07-30 14:00:00 PM', triggerType: 'Webhook' as TriggerType },
];

// Helper to map workflow status text to StatusIndicator's 'status' prop values
const mapWorkflowStatusToIndicator = (status: WorkflowStatus): string => {
  switch (status) {
    case 'Active': return 'active'; // Maps to green
    case 'Paused': return 'idle';   // Maps to yellow
    case 'Error': return 'error';   // Maps to red
    default: return 'offline';      // Default, though all mock data has defined statuses
  }
};

// Helper to get icon for trigger type
const TriggerIcon = ({ type }: { type: TriggerType }) => {
  switch (type) {
    case 'Scheduled': return <Clock className="mr-2 h-4 w-4 text-blue-500" />;
    case 'Webhook': return <Zap className="mr-2 h-4 w-4 text-purple-500" />;
    case 'Manual': return <Play className="mr-2 h-4 w-4 text-gray-500" />; // Using Play for Manual
    default: return null;
  }
};


export function WorkflowsPage() {
  // Placeholder for handling actions
  const handleAction = (action: string, workflowId: string, workflowName?: string) => {
    const message = `${action} action triggered for workflow ID: ${workflowId}` + (workflowName ? ` (Name: ${workflowName})` : '');
    alert(message);
    console.log(message);
  };

  return (
    <PageWrapper title="Workflows Management">
      <div className="flex items-center justify-between mb-6">
        <p className="text-muted-foreground">
          Automate tasks by creating, managing, and monitoring your workflows.
        </p>
        <Button asChild>
          <Link to="/workflows/new"> {/* Assuming a route for creating new workflows */}
            <PlusCircle className="mr-2 h-4 w-4" /> Create Workflow
          </Link>
        </Button>
      </div>

      <div className="bg-card p-0 border rounded-lg shadow-sm"> {/* p-0 for table to span full width */}
        <div className="overflow-x-auto"> {/* For responsiveness on smaller screens */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead className="min-w-[250px] lg:min-w-[300px] xl:min-w-[350px]">Description</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead>Trigger</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockWorkflows.map((workflow) => (
                <TableRow key={workflow.id}>
                  <TableCell className="font-medium">{workflow.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                     <div className="truncate w-full max-w-xs md:max-w-sm lg:max-w-md xl:max-w-lg" title={workflow.description}>
                       {workflow.description}
                     </div>
                  </TableCell>
                  <TableCell>
                    <StatusIndicator
                      status={mapWorkflowStatusToIndicator(workflow.status)}
                      text={workflow.status}
                    />
                  </TableCell>
                  <TableCell className="text-xs font-mono">{workflow.lastRun}</TableCell>
                  <TableCell className="text-sm">
                    <div className="flex items-center">
                      <TriggerIcon type={workflow.triggerType} />
                      {workflow.triggerType}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu for {workflow.name}</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions for {workflow.name}</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleAction('View Runs', workflow.id, workflow.name)}>
                          <Eye className="mr-2 h-4 w-4" /> View Runs
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Edit Workflow', workflow.id, workflow.name)}>
                          <Edit className="mr-2 h-4 w-4" /> Edit Workflow
                        </DropdownMenuItem>
                         <DropdownMenuItem onClick={() => handleAction('Run Now', workflow.id, workflow.name)}>
                          <Play className="mr-2 h-4 w-4" /> Run Now
                        </DropdownMenuItem>
                        {workflow.status === 'Active' && (
                          <DropdownMenuItem onClick={() => handleAction('Pause', workflow.id, workflow.name)}>
                            <Pause className="mr-2 h-4 w-4" /> Pause
                          </DropdownMenuItem>
                        )}
                        {workflow.status === 'Paused' && (
                          <DropdownMenuItem onClick={() => handleAction('Resume', workflow.id, workflow.name)}>
                            <Play className="mr-2 h-4 w-4" /> Resume
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleAction('Delete Workflow', workflow.id, workflow.name)}
                          className="text-destructive hover:!bg-destructive/10 focus:!bg-destructive/10 focus:!text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" /> Delete Workflow
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
      {/* TODO: Implement pagination if workflow list grows */}
    </PageWrapper>
  );
}
