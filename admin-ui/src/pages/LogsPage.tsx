import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { RefreshCw } from 'lucide-react';
import { useLogs } from '@/lib/api';

export function LogsPage() {
  // State for filters
  const [searchTerm, setSearchTerm] = React.useState('');
  const [logLevelFilter, setLogLevelFilter] = React.useState('all');
  const [dateRangeFilter, setDateRangeFilter] = React.useState('all');
  const [limit, setLimit] = React.useState(50);

  const { data: logsData = [], refetch } = useLogs(limit);

  // Filter logs based on search and filters
  const filteredLogs = React.useMemo(() => {
    return logsData.filter((log: any) => {
      // Search filter
      if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase()) &&
          !log.source.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Level filter
      if (logLevelFilter !== 'all' && log.level.toLowerCase() !== logLevelFilter) {
        return false;
      }
      
      return true;
    });
  }, [logsData, searchTerm, logLevelFilter]);

  const handleApplyFilters = () => {
    refetch();
  };

  // Get level badge variant
  const getLevelVariant = (level: string) => {
    switch(level.toUpperCase()) {
      case 'ERROR': return 'destructive';
      case 'WARN': return 'warning';
      case 'INFO': return 'default';
      case 'DEBUG': return 'secondary';
      default: return 'outline';
    }
  };

  return (
    <PageWrapper title="System Logs">
      {/* Filter/Search Section */}
      <div className="bg-card p-4 rounded-lg shadow-sm mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="space-y-1">
            <label htmlFor="search-logs" className="text-sm font-medium text-muted-foreground">Search Logs</label>
            <Input
              id="search-logs"
              placeholder="By message, source..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="log-level-select" className="text-sm font-medium text-muted-foreground">Log Level</label>
            <Select value={logLevelFilter} onValueChange={setLogLevelFilter}>
              <SelectTrigger id="log-level-select"><SelectValue placeholder="Log Level" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="info">INFO</SelectItem>
                <SelectItem value="warn">WARN</SelectItem>
                <SelectItem value="error">ERROR</SelectItem>
                <SelectItem value="debug">DEBUG</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <label htmlFor="date-range-select" className="text-sm font-medium text-muted-foreground">Date Range</label>
            <Select value={dateRangeFilter} onValueChange={setDateRangeFilter}>
              <SelectTrigger id="date-range-select"><SelectValue placeholder="Date Range" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Time</SelectItem>
                <SelectItem value="hour">Last Hour</SelectItem>
                <SelectItem value="day">Last 24 Hours</SelectItem>
                <SelectItem value="week">Last 7 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleApplyFilters}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Apply Filters
          </Button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-card p-0 border rounded-lg shadow-sm">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px] min-w-[180px]">Timestamp</TableHead>
                <TableHead className="w-[100px] min-w-[100px]">Level</TableHead>
                <TableHead className="w-[150px] min-w-[150px]">Source</TableHead>
                <TableHead className="min-w-[300px]">Message</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log: any, index: number) => (
                <TableRow key={`log-${index}`}>
                  <TableCell className="text-xs text-muted-foreground font-mono">
                    {new Date(log.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getLevelVariant(log.level) as any}>
                      {log.level}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium text-sm">{log.source}</TableCell>
                  <TableCell className="text-sm">
                    <div className="max-w-xl">
                      {log.message}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Info and Controls */}
      <div className="mt-6 flex justify-between items-center">
        <div className="text-sm text-muted-foreground">
          Showing {filteredLogs.length} of {logsData.length} logs • Auto-refreshing every 5 seconds
        </div>
        <div className="flex items-center gap-2">
          <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="25">25 logs</SelectItem>
              <SelectItem value="50">50 logs</SelectItem>
              <SelectItem value="100">100 logs</SelectItem>
              <SelectItem value="200">200 logs</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </PageWrapper>
  );
}
