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
 * Agent Registry component that provides management of AI agents
 */
const AgentRegistry = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "active" | "inactive"
  >("all");

  // Sample agent data
  const agents = [
    {
      id: "agent-001",
      name: "Content Creator",
      description: "Creates high-quality content based on provided topics",
      status: "active",
      type: "content",
      lastActive: "10 minutes ago",
      conversations: 1245,
      avgResponseTime: "2.3s",
    },
    {
      id: "agent-002",
      name: "Research Assistant",
      description: "Performs in-depth research on specified topics",
      status: "active",
      type: "research",
      lastActive: "5 minutes ago",
      conversations: 987,
      avgResponseTime: "3.1s",
    },
    {
      id: "agent-003",
      name: "Data Analyst",
      description: "Analyzes data and provides insights",
      status: "active",
      type: "analysis",
      lastActive: "30 minutes ago",
      conversations: 756,
      avgResponseTime: "2.8s",
    },
    {
      id: "agent-004",
      name: "Project Manager",
      description: "Helps plan and organize projects",
      status: "inactive",
      type: "planning",
      lastActive: "2 days ago",
      conversations: 432,
      avgResponseTime: "2.5s",
    },
    {
      id: "agent-005",
      name: "Creative Writer",
      description: "Generates creative content and stories",
      status: "active",
      type: "creative",
      lastActive: "1 hour ago",
      conversations: 654,
      avgResponseTime: "2.7s",
    },
    {
      id: "agent-006",
      name: "Customer Support",
      description: "Provides customer support and answers questions",
      status: "inactive",
      type: "support",
      lastActive: "3 days ago",
      conversations: 321,
      avgResponseTime: "1.9s",
    },
  ];

  // Filter agents based on search query and status filter
  const filteredAgents = agents.filter((agent) => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      filterStatus === "all" || agent.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Agent Registry</h2>
        <Button>Create New Agent</Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col space-y-4 md:flex-row md:space-x-4 md:space-y-0">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search agents..."
                className="w-full rounded-md border border-input bg-background px-3 py-2"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              className="rounded-md border border-input bg-background px-3 py-2"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Agent List */}
      <Card>
        <CardHeader>
          <CardTitle>Agents</CardTitle>
          <CardDescription>
            {filteredAgents.length} agents found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAgents.length === 0 ? (
              <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">No agents found</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <div className="grid grid-cols-12 gap-4 border-b bg-muted/50 p-4 font-medium">
                  <div className="col-span-4">Name</div>
                  <div className="col-span-2">Type</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-2">Last Active</div>
                  <div className="col-span-2">Actions</div>
                </div>
                {filteredAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="grid grid-cols-12 gap-4 border-b p-4 last:border-0"
                  >
                    <div className="col-span-4">
                      <div className="font-medium">{agent.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {agent.description}
                      </div>
                    </div>
                    <div className="col-span-2 flex items-center">
                      <span className="capitalize">{agent.type}</span>
                    </div>
                    <div className="col-span-2 flex items-center">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          agent.status === "active"
                            ? "bg-status-healthy/10 text-status-healthy"
                            : "bg-status-inactive/10 text-status-inactive"
                        }`}
                      >
                        {agent.status === "active" ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <div className="col-span-2 flex items-center text-sm">
                      {agent.lastActive}
                    </div>
                    <div className="col-span-2 flex items-center space-x-2">
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                      <Button variant="outline" size="sm">
                        Edit
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Agent Analytics */}
      <Tabs defaultValue="activity" className="space-y-4">
        <TabsList>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
        </TabsList>
        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>Conversation volume over time</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "Jan 1", value: 1200 },
                  { name: "Jan 5", value: 1800 },
                  { name: "Jan 10", value: 1400 },
                  { name: "Jan 15", value: 2200 },
                  { name: "Jan 20", value: 1900 },
                  { name: "Jan 25", value: 2400 },
                  { name: "Jan 30", value: 2100 },
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
              <CardTitle>Agent Performance</CardTitle>
              <CardDescription>
                Average response time by agent type
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <BarChart
                data={[
                  { name: "Content", value: 2.3 },
                  { name: "Research", value: 3.1 },
                  { name: "Analysis", value: 2.8 },
                  { name: "Planning", value: 2.5 },
                  { name: "Creative", value: 2.7 },
                  { name: "Support", value: 1.9 },
                ]}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="distribution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Distribution</CardTitle>
              <CardDescription>Distribution of agents by type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
                {[
                  { type: "Content", count: 8, color: "bg-primary" },
                  { type: "Research", count: 6, color: "bg-secondary" },
                  { type: "Analysis", count: 4, color: "bg-memory-hot" },
                  { type: "Planning", count: 3, color: "bg-memory-warm" },
                  { type: "Creative", count: 5, color: "bg-memory-cold" },
                  { type: "Support", count: 2, color: "bg-status-inactive" },
                ].map((item) => (
                  <div key={item.type} className="flex flex-col space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{item.type}</span>
                      <span className="text-sm text-muted-foreground">
                        {item.count}
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-secondary">
                      <div
                        className={`h-2 rounded-full ${item.color}`}
                        style={{ width: `${(item.count / 8) * 100}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Agent Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
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
            <div className="text-2xl font-bold">{agents.length}</div>
            <p className="text-xs text-muted-foreground">+2 from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
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
            <div className="text-2xl font-bold">
              {agents.filter((a) => a.status === "active").length}
            </div>
            <p className="text-xs text-muted-foreground">+1 from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Conversations
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
            <div className="text-2xl font-bold">
              {formatNumber(
                agents.reduce((sum, agent) => sum + agent.conversations, 0),
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              +12% from last month
            </p>
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
            <div className="text-2xl font-bold">2.5s</div>
            <p className="text-xs text-muted-foreground">
              -0.3s from last month
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AgentRegistry;
