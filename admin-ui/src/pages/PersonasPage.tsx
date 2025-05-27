import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { MoreHorizontal, Edit, Trash2, Eye, Copy, PlusCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from '@tanstack/react-router'; // For "Create Persona" button link

// Mock Data
const mockPersonas = [
  { id: 'per_001', name: 'Helpful Assistant', description: 'A friendly and helpful assistant for general queries, providing clear and concise answers.', version: '1.2.1', lastUpdated: '2024-07-28 10:00 AM' },
  { id: 'per_002', name: 'Sarcastic Bot 3000', description: 'Witty and sarcastic responses, primarily for entertainment and engaging users in a humorous way.', version: '0.9.5', lastUpdated: '2024-07-25 14:30 PM' },
  { id: 'per_003', name: 'Technical Expert AI', description: 'Provides in-depth technical explanations and troubleshooting steps for software and hardware issues.', version: '2.1.0', lastUpdated: '2024-07-29 09:15 AM' },
  { id: 'per_004', name: 'Creative Storyteller', description: 'Generates imaginative stories, poems, and other creative content based on user prompts.', version: '1.0.3', lastUpdated: '2024-07-22 18:00 PM' },
  { id: 'per_005', name: 'Empathetic Listener', description: 'Offers supportive and understanding responses, designed for well-being and mental health support.', version: '1.5.0', lastUpdated: '2024-07-29 11:45 AM' },
  { id: 'per_006', name: 'Formal Business Analyst', description: 'Delivers data-driven insights and business analysis in a formal and professional tone.', version: '0.8.2', lastUpdated: '2024-07-26 16:00 PM' },
];

export function PersonasPage() {
  // Placeholder for handling actions
  const handleAction = (action: string, personaId: string) => {
    alert(`${action} action triggered for persona ${personaId}`);
    console.log(`${action} action for persona ${personaId}`);
  };

  return (
    <PageWrapper title="Personas Management">
      <div className="flex items-center justify-between mb-6">
        <p className="text-muted-foreground">
          Define, manage, and version control your AI agent personas.
        </p>
        <Button asChild>
          <Link to="/personas/new"> {/* Assuming a route for creating new personas */}
            <PlusCircle className="mr-2 h-4 w-4" /> Create Persona
          </Link>
        </Button>
      </div>

      <div className="bg-card p-0 border rounded-lg shadow-sm"> {/* p-0 for table to span full width */}
        <div className="overflow-x-auto"> {/* For responsiveness on smaller screens */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Persona ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="min-w-[250px] lg:min-w-[300px] xl:min-w-[400px]">Description</TableHead> {/* Provide min-width for description */}
                <TableHead>Version</TableHead>
                <TableHead>Last Updated</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockPersonas.map((persona) => (
                <TableRow key={persona.id}>
                  <TableCell className="font-mono text-xs">{persona.id}</TableCell>
                  <TableCell className="font-medium">{persona.name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    <div className="truncate w-full max-w-xs md:max-w-sm lg:max-w-md xl:max-w-lg" title={persona.description}>
                      {persona.description}
                    </div>
                  </TableCell>
                  <TableCell>{persona.version}</TableCell>
                  <TableCell>{persona.lastUpdated}</TableCell>
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
                        <DropdownMenuItem onClick={() => handleAction('View Details', persona.id)}>
                          <Eye className="mr-2 h-4 w-4" /> View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Edit', persona.id)}>
                          <Edit className="mr-2 h-4 w-4" /> Edit Persona
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleAction('Duplicate', persona.id)}>
                          <Copy className="mr-2 h-4 w-4" /> Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => handleAction('Delete', persona.id)}
                          className="text-destructive hover:!bg-destructive/10 focus:!bg-destructive/10 focus:!text-destructive"
                        >
                          <Trash2 className="mr-2 h-4 w-4" /> Delete Persona
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
      {/* TODO: Implement pagination if persona list grows */}
    </PageWrapper>
  );
}
