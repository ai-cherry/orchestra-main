import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data
const personasData = [
  { id: '1', name: 'Customer Support', description: 'Friendly and helpful support agent', lastUsed: '2 hours ago' },
  { id: '2', name: 'Technical Expert', description: 'Detailed technical knowledge provider', lastUsed: '1 day ago' },
  { id: '3', name: 'Creative Writer', description: 'Content creation specialist', lastUsed: '3 hours ago' },
  { id: '4', name: 'Data Analyst', description: 'Analytical insights provider', lastUsed: '5 days ago' },
  { id: '5', name: 'Executive Summary', description: 'Concise business information', lastUsed: '12 hours ago' },
  { id: '6', name: 'Sales Representative', description: 'Persuasive product promoter', lastUsed: '2 days ago' },
];

export function PersonasPage() {
  return (
    <PageWrapper title="Personas">
      <div className="flex flex-col space-y-6">
        {/* Header with search and actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search personas..."
              className="w-full rounded-md pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
          <Button asChild>
            <Link to="/personas">
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh Personas
            </Link>
          </Button>
        </div>

        {/* Main content */}
        <Card>
          <CardHeader>
            <CardTitle>Persona Library</CardTitle>
            <CardDescription>Manage and customize agent personas.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {personasData.map((persona) => (
                  <TableRow key={persona.id}>
                    <TableCell className="font-medium">{persona.name}</TableCell>
                    <TableCell>{persona.description}</TableCell>
                    <TableCell>{persona.lastUsed}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">Edit</Button>
                      <Button variant="ghost" size="sm">Use</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{personasData.length}</strong> personas
            </div>
            <div className="space-x-2">
              <Button variant="outline" size="sm" disabled>Previous</Button>
              <Button variant="outline" size="sm" disabled>Next</Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </PageWrapper>
  );
}
