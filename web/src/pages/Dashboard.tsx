export function Dashboard() {
  return (
    <div className="flex flex-col h-full bg-background">
      <div className="border-b border-border p-6">
        <h1 className="text-2xl font-bold">System Dashboard</h1>
        <p className="text-muted-foreground">Monitor system performance and agent activity</p>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-2">Active Agents</h3>
            <p className="text-2xl font-bold text-primary">3</p>
          </div>
          
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-2">Files Processed</h3>
            <p className="text-2xl font-bold text-green-500">127</p>
          </div>
          
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-2">System Status</h3>
            <p className="text-2xl font-bold text-green-500">Operational</p>
          </div>
        </div>
      </div>
    </div>
  )
} 