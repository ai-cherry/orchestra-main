import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs'
import { AreaChart, LineChart } from '../../components/ui/charts'
import { formatBytes, formatNumber } from '../../lib/utils'

/**
 * Memory Management component that provides detailed visibility into the memory system
 */
const MemoryManagement = () => {
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d'>('24h')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Memory Management</h2>
        <div className="flex items-center space-x-2">
          <select
            className="rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as '24h' | '7d' | '30d')}
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Memory Tier Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-l-4 border-l-memory-hot">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Hot Tier</CardTitle>
            <CardDescription>Redis In-Memory Cache</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85%</div>
            <div className="text-sm text-muted-foreground">
              {formatBytes(850 * 1024 * 1024)} / {formatBytes(1 * 1024 * 1024 * 1024)}
            </div>
            <div className="mt-4 h-1 w-full rounded-full bg-secondary">
              <div className="h-1 w-[85%] rounded-full bg-memory-hot"></div>
            </div>
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <div>Hit Rate: 92%</div>
              <div>Avg. Latency: 2ms</div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-memory-warm">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Warm Tier</CardTitle>
            <CardDescription>Firestore Storage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">42%</div>
            <div className="text-sm text-muted-foreground">
              {formatBytes(1.26 * 1024 * 1024 * 1024)} / {formatBytes(3 * 1024 * 1024 * 1024)}
            </div>
            <div className="mt-4 h-1 w-full rounded-full bg-secondary">
              <div className="h-1 w-[42%] rounded-full bg-memory-warm"></div>
            </div>
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <div>Hit Rate: 78%</div>
              <div>Avg. Latency: 120ms</div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-memory-cold">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Cold Tier</CardTitle>
            <CardDescription>Compressed Storage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">28%</div>
            <div className="text-sm text-muted-foreground">
              {formatBytes(1.12 * 1024 * 1024 * 1024)} / {formatBytes(4 * 1024 * 1024 * 1024)}
            </div>
            <div className="mt-4 h-1 w-full rounded-full bg-secondary">
              <div className="h-1 w-[28%] rounded-full bg-memory-cold"></div>
            </div>
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <div>Hit Rate: 45%</div>
              <div>Avg. Latency: 350ms</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Memory Usage Charts */}
      <Card>
        <CardHeader>
          <CardTitle>Memory Usage Over Time</CardTitle>
          <CardDescription>
            Usage trends across all memory tiers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <AreaChart
              data={[
                { name: "00:00", hot: 75, warm: 40, cold: 25 },
                { name: "04:00", hot: 80, warm: 40, cold: 25 },
                { name: "08:00", hot: 85, warm: 42, cold: 26 },
                { name: "12:00", hot: 70, warm: 45, cold: 28 },
                { name: "16:00", hot: 90, warm: 42, cold: 28 },
                { name: "20:00", hot: 85, warm: 42, cold: 28 },
                { name: "24:00", hot: 82, warm: 42, cold: 28 },
              ]}
              categories={["hot", "warm", "cold"]}
              colors={["#ef4444", "#f59e0b", "#3b82f6"]}
              xAxisKey="name"
              className="h-[300px]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Tabs defaultValue="operations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations">Operations</TabsTrigger>
          <TabsTrigger value="latency">Latency</TabsTrigger>
          <TabsTrigger value="pruning">Context Pruning</TabsTrigger>
        </TabsList>
        <TabsContent value="operations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Memory Operations</CardTitle>
              <CardDescription>
                Read and write operations across memory tiers
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "00:00", reads: 1245, writes: 450 },
                  { name: "04:00", reads: 980, writes: 320 },
                  { name: "08:00", reads: 1540, writes: 520 },
                  { name: "12:00", reads: 1860, writes: 640 },
                  { name: "16:00", reads: 2100, writes: 720 },
                  { name: "20:00", reads: 1750, writes: 580 },
                  { name: "24:00", reads: 1320, writes: 420 },
                ]}
                xAxisKey="name"
                yAxisKey="reads"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="latency" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Memory Latency</CardTitle>
              <CardDescription>
                Average latency by tier over time
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "00:00", hot: 2, warm: 115, cold: 340 },
                  { name: "04:00", hot: 2, warm: 118, cold: 345 },
                  { name: "08:00", hot: 3, warm: 125, cold: 350 },
                  { name: "12:00", hot: 4, warm: 130, cold: 360 },
                  { name: "16:00", hot: 3, warm: 122, cold: 355 },
                  { name: "20:00", hot: 2, warm: 120, cold: 350 },
                  { name: "24:00", hot: 2, warm: 118, cold: 345 },
                ]}
                xAxisKey="name"
                yAxisKey="hot"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="pruning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Context Pruning</CardTitle>
              <CardDescription>
                Context pruning activity and token savings
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "00:00", pruned: 120, saved: 24000 },
                  { name: "04:00", pruned: 85, saved: 17000 },
                  { name: "08:00", pruned: 150, saved: 30000 },
                  { name: "12:00", pruned: 210, saved: 42000 },
                  { name: "16:00", pruned: 180, saved: 36000 },
                  { name: "20:00", pruned: 140, saved: 28000 },
                  { name: "24:00", pruned: 110, saved: 22000 },
                ]}
                xAxisKey="name"
                yAxisKey="pruned"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Recent Memory Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Memory Events</CardTitle>
          <CardDescription>
            Latest memory system events and operations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                title: "Memory Pressure Alert",
                description: "Hot tier memory usage at 85%",
                time: "10 minutes ago",
                type: "warning"
              },
              {
                title: "Tier Migration",
                description: "Migrated 250MB from hot to warm tier",
                time: "30 minutes ago",
                type: "info"
              },
              {
                title: "Context Pruning",
                description: "Pruned 120 conversation contexts, saved 24K tokens",
                time: "1 hour ago",
                type: "success"
              },
              {
                title: "Cache Eviction",
                description: "LRU cache evicted 50MB of data",
                time: "2 hours ago",
                type: "info"
              },
              {
                title: "Cold Tier Compression",
                description: "Compressed 100MB of cold tier data, 40% space saved",
                time: "3 hours ago",
                type: "success"
              }
            ].map((event, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div className={`mt-0.5 h-2 w-2 rounded-full bg-status-${event.type === "warning" ? "warning" : event.type === "success" ? "healthy" : "info"}`} />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {event.title}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {event.description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {event.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default MemoryManagement
