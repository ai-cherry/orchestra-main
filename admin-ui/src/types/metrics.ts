export interface SystemMetrics {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime: string;
    // Add other fields like network stats, db stats if available from /api/metrics
}

export interface AgentMetric {
    id: string;
    name: string;
    type: string;
    status: 'active' | 'inactive' | 'error' | 'starting' | 'stopping';
    lastRun: string; // ISO date string
    tasks_completed?: number;
    memory_usage?: number;
    // other agent fields
} 