import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator'; // Already adapted for log levels

// Mock Data
const mockLogs = [
  { id: 'log_001', timestamp: '2024-07-30 10:00:00', level: 'INFO', source: 'AgentService', message: 'Agent X (ID: agt_123) started successfully and is now processing data stream alpha.' },
  { id: 'log_002', timestamp: '2024-07-30 10:01:15', level: 'WARN', source: 'APIService', message: 'Rate limit approaching for external API (XYZ-Weather). Current usage: 85%.' },
  { id: 'log_003', timestamp: '2024-07-30 10:02:30', level: 'ERROR', source: 'DatabaseConnector', message: 'Failed to connect to primary database cluster (db-main-01) after 3 retries. Error: Connection timeout.' },
  { id: 'log_004', timestamp: '2024-07-30 10:03:45', level: 'INFO', source: 'WorkflowEngine', message: 'Workflow "DailyReportGen" (ID: wf_789) completed successfully in 12.5s.' },
  { id: 'log_005', timestamp: '2024-07-30 10:05:00', level: 'DEBUG', source: 'AgentService', message: 'Received new task for Agent Y (ID: agt_456): Process input file input.csv. Payload size: 2.5MB.' }, // Debug is not explicitly mapped, will use default
  { id: 'log_006', timestamp: '2024-07-30 10:06:20', level: 'INFO', source: 'APIService', message: 'User admin@example.com authenticated successfully via OAuth2.' },
  { id: 'log_007', timestamp: '2024-07-30 10:07:50', level: 'WARN', source: 'ResourceMonitor', message: 'Memory usage for Agent Z (ID: agt_789) at 92%. Threshold is 90%.' },
  { id: 'log_008', timestamp: '2024-07-30 10:08:30', level: 'ERROR', source: 'AgentService', message: 'Unhandled exception in Agent X (ID: agt_123) while processing task task_abc. Error: NullPointerException at processData:123.' },
  { id: 'log_009', timestamp: '2024-07-30 10:10:00', level: 'INFO', source: 'System', message: 'Scheduled maintenance window starting in 1 hour.' },
  { id: 'log_010', timestamp: '2024-07-30 10:11:00', level: 'INFO', source: 'WorkflowEngine', message: 'Workflow "DataBackup" (ID: wf_001) initiated by system scheduler.' },
  { id: 'log_011', timestamp: '2024-07-30 10:12:00', level: 'WARN', source: 'SecurityService', message: 'Multiple failed login attempts for user `unknown_user` from IP 192.168.1.100.' },
  { id: 'log_012', timestamp: '2024-07-30 10:13:00', level: 'ERROR', source: 'PaymentGateway', message: 'Transaction failed for order ORD_123. Gateway error: Insufficient funds (Code: 51).' },
];

// The StatusIndicator component already handles mapping status to color,
// and the `text` prop will display the log level directly.
// So, `logLevelVariant` helper is not strictly needed if StatusIndicator is used as intended.
// The `status` prop of StatusIndicator will be 'info', 'warn', 'error'.

export function LogsPage() {
  // Placeholder state and handlers for filters
  const [searchTerm, setSearchTerm] = React.useState('');
  const [logLevelFilter, setLogLevelFilter] = React.useState('all');
  const [dateRangeFilter, setDateRangeFilter] = React.useState('all');

  const handleApplyFilters = () => {
    // In a real app, this would trigger data fetching with the selected filters
    alert(`Applying filters: Search='${searchTerm}', Level='${logLevelFilter}', Date='${dateRangeFilter}'`);
    console.log({ searchTerm, logLevelFilter, dateRangeFilter });
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
          <Button onClick={handleApplyFilters} className="w-full md:w-auto">Apply Filters</Button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-card p-0 border rounded-lg shadow-sm"> {/* p-0 for table to span full width */}
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
              {mockLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-xs text-muted-foreground font-mono">{log.timestamp}</TableCell>
                  <TableCell>
                    {/* Pass log.level (e.g., 'INFO') to status, and also as text for display */}
                    <StatusIndicator status={log.level.toLowerCase()} text={log.level.toUpperCase()} />
                  </TableCell>
                  <TableCell className="font-medium text-sm">{log.source}</TableCell>
                  <TableCell className="text-sm max-w-md lg:max-w-lg xl:max-w-xl">
                    <div className="truncate" title={log.message}>
                      {log.message}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Placeholder Pagination */}
      <div className="mt-6 flex justify-center items-center space-x-2">
        <Button variant="outline" size="sm" disabled>Previous</Button>
        <span className="text-sm text-muted-foreground">Page 1 of 10 (Placeholder)</span>
        <Button variant="outline" size="sm">Next</Button>
      </div>
    </PageWrapper>
  );
}
