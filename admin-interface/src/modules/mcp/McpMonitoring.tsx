import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import { BarChart, LineChart } from "../../components/ui/charts";
import { formatNumber } from "../../lib/utils";

/**
 * MCP Monitoring component that provides visibility into the Model Context Protocol system
 */
const McpMonitoring = () => {
  const [timeRange, setTimeRange] = useState<"1h" | "24h" | "7d">("24h");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">MCP Monitoring</h2>
        <div className="flex items-center space-x-2">
          <select
            className="rounded-md border border-input bg-background px-3 py-1 text-sm"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </select>
        </div>
      </div>

      {/* MCP Server Status */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Server Status</CardTitle>
            <div className="h-2 w-2 rounded-full bg-status-healthy"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Healthy</div>
            <p className="text-xs text-muted-foreground">
              Uptime: 7 days, 14 hours
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Connected Tools
            </CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
            <p className="text-xs text-muted-foreground">+2 from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Memory Operations
            </CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatNumber(24567)}</div>
            <p className="text-xs text-muted-foreground">+19% from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Response Time
            </CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">45ms</div>
            <p className="text-xs text-muted-foreground">
              -12ms from last week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Connected Tools */}
      <Card>
        <CardHeader>
          <CardTitle>Connected Tools</CardTitle>
          <CardDescription>
            Tools currently connected to the MCP server
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <div className="grid grid-cols-12 gap-4 border-b bg-muted/50 p-4 font-medium">
              <div className="col-span-3">Tool Name</div>
              <div className="col-span-3">Type</div>
              <div className="col-span-2">Status</div>
              <div className="col-span-2">Memory Usage</div>
              <div className="col-span-2">Actions</div>
            </div>
            {[
              {
                name: "Roo",
                type: "LLM Assistant",
                status: "active",
                memoryUsage: "16 MB",
              },
              {
                name: "Cline",
                type: "IDE Integration",
                status: "active",
                memoryUsage: "8 MB",
              },
              {
                name: "Gemini Pro",
                type: "LLM Provider",
                status: "active",
                memoryUsage: "4 MB",
              },
              {
                name: "GPT-4",
                type: "LLM Provider",
                status: "active",
                memoryUsage: "4 MB",
              },
              {
                name: "Claude 3",
                type: "LLM Provider",
                status: "active",
                memoryUsage: "4 MB",
              },
              {
                name: "GitHub Copilot",
                type: "Code Assistant",
                status: "active",
                memoryUsage: "8 MB",
              },
              {
                name: "Vector Search",
                type: "Search Provider",
                status: "active",
                memoryUsage: "12 MB",
              },
              {
                name: "Semantic Cache",
                type: "Cache Provider",
                status: "active",
                memoryUsage: "24 MB",
              },
            ].map((tool, index) => (
              <div
                key={index}
                className="grid grid-cols-12 gap-4 border-b p-4 last:border-0"
              >
                <div className="col-span-3 font-medium">{tool.name}</div>
                <div className="col-span-3">{tool.type}</div>
                <div className="col-span-2">
                  <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-status-healthy/10 text-status-healthy">
                    {tool.status}
                  </span>
                </div>
                <div className="col-span-2">{tool.memoryUsage}</div>
                <div className="col-span-2">
                  <Button variant="outline" size="sm">
                    Details
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* MCP Analytics */}
      <Tabs defaultValue="operations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations">Operations</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="memory">Memory Usage</TabsTrigger>
        </TabsList>
        <TabsContent value="operations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>MCP Operations</CardTitle>
              <CardDescription>Operation volume over time</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "00:00", value: 1245 },
                  { name: "04:00", value: 980 },
                  { name: "08:00", value: 1540 },
                  { name: "12:00", value: 1860 },
                  { name: "16:00", value: 2100 },
                  { name: "20:00", value: 1750 },
                  { name: "24:00", value: 1320 },
                ]}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Response Time</CardTitle>
              <CardDescription>Average response time by tool</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <BarChart
                data={[
                  { name: "Roo", value: 45 },
                  { name: "Cline", value: 38 },
                  { name: "Gemini Pro", value: 120 },
                  { name: "GPT-4", value: 150 },
                  { name: "Claude 3", value: 135 },
                  { name: "GitHub Copilot", value: 42 },
                  { name: "Vector Search", value: 65 },
                  { name: "Semantic Cache", value: 15 },
                ]}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="memory" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Memory Usage</CardTitle>
              <CardDescription>Memory usage by tool</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { name: "Roo", usage: 16, percentage: 20 },
                  { name: "Cline", usage: 8, percentage: 10 },
                  { name: "Gemini Pro", usage: 4, percentage: 5 },
                  { name: "GPT-4", usage: 4, percentage: 5 },
                  { name: "Claude 3", usage: 4, percentage: 5 },
                  { name: "GitHub Copilot", usage: 8, percentage: 10 },
                  { name: "Vector Search", usage: 12, percentage: 15 },
                  { name: "Semantic Cache", usage: 24, percentage: 30 },
                ].map((item) => (
                  <div key={item.name} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-sm font-medium">{item.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-muted-foreground">
                          {item.usage} MB
                        </span>
                        <span className="text-xs text-muted-foreground">
                          ({item.percentage}%)
                        </span>
                      </div>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary">
                      <div
                        className="h-2 rounded-full bg-primary"
                        style={{ width: `${item.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* MCP Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent MCP Events</CardTitle>
          <CardDescription>Latest events from the MCP server</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                title: "Tool Connected",
                description: "Semantic Cache connected to MCP server",
                time: "10 minutes ago",
                type: "info",
              },
              {
                title: "Memory Sync",
                description: "Synchronized memory between Roo and Cline",
                time: "15 minutes ago",
                type: "info",
              },
              {
                title: "Performance Alert",
                description: "GPT-4 response time exceeded threshold (150ms)",
                time: "30 minutes ago",
                type: "warning",
              },
              {
                title: "Memory Shared",
                description: "Shared context between Roo and Vector Search",
                time: "45 minutes ago",
                type: "info",
              },
              {
                title: "Tool Reconnected",
                description:
                  "GitHub Copilot reconnected after temporary disconnect",
                time: "1 hour ago",
                type: "info",
              },
            ].map((event, index) => (
              <div key={index} className="flex items-start space-x-4">
                <div
                  className={`mt-0.5 h-2 w-2 rounded-full bg-status-${event.type === "warning" ? "warning" : event.type === "success" ? "healthy" : "info"}`}
                />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {event.title}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {event.description}
                  </p>
                  <p className="text-xs text-muted-foreground">{event.time}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default McpMonitoring;
