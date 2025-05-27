import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator'; // Ensure this path is correct
import { MoreHorizontal, Edit, Trash2, Eye, Download, RefreshCw, PlusCircle, FileText, Link as LinkIcon, FileArchive, FileUp, FileQuestion } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel, // Added for consistency
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from '@tanstack/react-router'; // For "Add Resource" button link

type ResourceStatus = 'Available' | 'Processing' | 'Error' | 'Archived';
type ResourceType = 'PDF' | 'URL' | 'ZIP' | 'Text' | 'Video' | 'Image' | 'Unknown';

// Helper to get an icon based on resource type
const getResourceTypeIcon = (type: ResourceType) => {
  const iconProps = { className: "h-5 w-5 text-muted-foreground" };
  switch (type) {
    case 'PDF': return <FileText {...iconProps} />;
    case 'URL': return <LinkIcon {...iconProps} />;
    case 'ZIP': return <FileArchive {...iconProps} />;
    case 'Text': return <FileText {...iconProps} />; // Could use a more specific icon if available
    case 'Video': return <FileText {...iconProps} />; // Placeholder, could use Film or Video icon
    case 'Image': return <FileText {...iconProps} />; // Placeholder, could use Image icon
    default: return <FileQuestion {...iconProps} />; // For Unknown type
  }
};

// Mock Data
const mockResources = [
  { id: 'res_001', name: 'Product Catalog Q4.pdf', type: 'PDF' as ResourceType, size: '2.5 MB', dateAdded: '2024-07-20', status: 'Available' as ResourceStatus },
  { id: 'res_002', name: 'Competitor Analysis Homepage', type: 'URL' as ResourceType, size: 'N/A', dateAdded: '2024-07-18', status: 'Processing' as ResourceStatus },
  { id: 'res_003', name: 'Brand Assets Archive.zip', type: 'ZIP' as ResourceType, size: '15.2 MB', dateAdded: '2024-07-15', status: 'Error' as ResourceStatus },
  { id: 'res_004', name: 'Onboarding Guide.txt', type: 'Text' as ResourceType, size: '120 KB', dateAdded: '2024-07-22', status: 'Available' as ResourceStatus },
  { id: 'res_005', name: 'Demo Video Showcase.mp4', type: 'Video' as ResourceType, size: '128 MB', dateAdded: '2024-07-10', status: 'Archived' as ResourceStatus }, // Archived will use default gray
  { id: 'res_006', name: 'System Architecture Diagram.png', type: 'Image' as ResourceType, size: '1.1 MB', dateAdded: '2024-07-05', status: 'Available' as ResourceStatus },
  { id: 'res_007', name: 'API Documentation Link', type: 'URL' as ResourceType, size: 'N/A', dateAdded: '2024-06-30', status: 'Available' as ResourceStatus },
];

// Helper to map resource status text to StatusIndicator's 'status' prop values
const mapResourceStatusToIndicator = (status: ResourceStatus): string => {
  switch (status) {
    case 'Available': return 'active';    // Maps to green
    case 'Processing': return 'info';     // Maps to blue (updated from 'idle')
    case 'Error': return 'error';       // Maps to red
    case 'Archived': return 'offline';   // Maps to gray
    default: return 'offline';          // Default for any other status
  }
};

export function ResourcesPage() {
  // Placeholder for handling actions
  const handleAction = (action: string, resourceId: string, resourceName?: string) => {
    const message = `${action} action triggered for resource ID: ${resourceId}` + (resourceName ? ` (Name: ${resourceName})` : '');
    alert(message);
    console.log(message);
  };

  return (
    <PageWrapper title="Resources Management"> {/* Using PageWrapper's title prop */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-muted-foreground">
          Manage data sources, knowledge bases, and other resources for your AI agents.
        </p>
        <Button asChild>
          <Link to="/resources/new"> {/* Assuming a route for adding new resources */}
            <FileUp className="mr-2 h-4 w-4" /> Add Resource {/* Changed icon to FileUp */}
          </Link>
        </Button>
      </div>

      <div className="bg-card p-0 border rounded-lg shadow-sm"> {/* p-0 for table to span full width */}
        <div className="overflow-x-auto"> {/* For responsiveness on smaller screens */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">Type</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Date Added</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockResources.map((resource) => (
                <TableRow key={resource.id}>
                  <TableCell>{getResourceTypeIcon(resource.type)}</TableCell>
                  <TableCell className="font-medium">{resource.name}</TableCell>
                  <TableCell>{resource.size}</TableCell>
                  <TableCell className="text-xs font-mono">{resource.dateAdded}</TableCell>
                  <TableCell>
                    <StatusIndicator 
                      status={mapResourceStatusToIndicator(resource.status)} 
                      text={resource.status} 
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                          <span className="sr-only">Open menu for {resource.name}</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions for {resource.name}</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => handleAction('View/Download', resource.id, resource.name)}>
                          <Download className="mr-2 h-4 w-4" /> View / Download
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Edit Metadata', resource.id, resource.name)}>
                          <Edit className="mr-2 h-4 w-4" /> Edit Metadata
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Re-process', resource.id, resource.name)}>
                          <RefreshCw className="mr-2 h-4 w-4" /> Re-process
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => handleAction('Delete Resource', resource.id, resource.name)}
                          className="text-destructive hover:!bg-destructive/10 focus:!bg-destructive/10 focus:!text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" /> Delete Resource
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
      {/* TODO: Implement pagination if resource list grows */}
    </PageWrapper>
  );
}
