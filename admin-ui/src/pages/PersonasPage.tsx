import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Search, RefreshCw } from 'lucide-react';
import { usePersonas } from '@/lib/api';

export function PersonasPage() {
  const { data: personasData = [], refetch } = usePersonas();

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
          <Button onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh Personas
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
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Capabilities</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {personasData.map((persona: any) => (
                  <TableRow key={persona.id}>
                    <TableCell className="font-medium">{persona.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{persona.agent_type}</Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">{persona.description}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {persona.capabilities.slice(0, 2).map((cap: string, idx: number) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {cap}
                          </Badge>
                        ))}
                        {persona.capabilities.length > 2 && (
                          <Badge variant="secondary" className="text-xs">
                            +{persona.capabilities.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={persona.active ? "default" : "secondary"}>
                        {persona.active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">Edit</Button>
                      <Button variant="ghost" size="sm" disabled={!persona.active}>Use</Button>
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
