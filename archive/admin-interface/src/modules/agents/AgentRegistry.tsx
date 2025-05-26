// AgentRegistry.tsx
// Complete, production-ready agent management UI with API integration, pagination, bulk actions, real-time status, and agent creation/edit modal.

import React, { useEffect, useState } from "react";
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

type Agent = {
  id: string;
  name: string;
  description: string;
  type: string;
  status: "active" | "inactive";
  last_active: string;
  conversations: number;
  avg_response_time: string;
};

const PAGE_SIZE = 10;

const AgentRegistry: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "active" | "inactive"
  >("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [showModal, setShowModal] = useState(false);
  const [modalAgent, setModalAgent] = useState<Agent | null>(null);

  // Fetch agents from backend API
  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        skip: String(page * PAGE_SIZE),
        limit: String(PAGE_SIZE),
        ...(searchQuery ? { search: searchQuery } : {}),
        ...(filterStatus !== "all" ? { status: filterStatus } : {}),
      });
      const res = await fetch(`/agents/?${params.toString()}`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAgents(data);
      setTotal(
        data.length < PAGE_SIZE && page === 0
          ? data.length
          : (page + 1) * PAGE_SIZE + (data.length === PAGE_SIZE ? 1 : 0),
      );
    } catch (e: any) {
      setError(e.message || "Failed to fetch agents.");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, filterStatus, page]);

  // Bulk selection logic
  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };
  const selectAll = () => setSelected(new Set(agents.map((a) => a.id)));
  const clearSelection = () => setSelected(new Set());

  // Bulk actions
  const handleBulkAction = async (
    action: "activate" | "deactivate" | "delete",
  ) => {
    if (selected.size === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/agents/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_ids: Array.from(selected), action }),
      });
      if (!res.ok) throw new Error(await res.text());
      await fetchAgents();
      clearSelection();
    } catch (e: any) {
      setError(e.message || "Bulk action failed.");
    }
    setLoading(false);
  };

  // Agent creation/edit modal logic
  const openCreateModal = () => {
    setModalAgent(null);
    setShowModal(true);
  };
  const openEditModal = (agent: Agent) => {
    setModalAgent(agent);
    setShowModal(true);
  };

  // Agent creation/edit form
  const AgentModal: React.FC = () => {
    const [form, setForm] = useState<Partial<Agent>>(modalAgent || {});
    const [valid, setValid] = useState(true);
    const [testResult, setTestResult] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    // Validate agent name uniqueness
    const validate = async () => {
      if (!form.name) return setValid(false);
      const res = await fetch("/agents/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          description: form.description || "",
          type: form.type || "",
        }),
      });
      const data = await res.json();
      setValid(data.valid);
    };

    // Test agent config
    const testAgent = async () => {
      setTestResult(null);
      const res = await fetch("/agents/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          description: form.description || "",
          type: form.type || "",
        }),
      });
      const data = await res.json();
      setTestResult(
        data.success ? "Test passed." : data.message || "Test failed.",
      );
    };

    // Submit create or update
    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setError(null);
      try {
        if (modalAgent) {
          // Update
          const res = await fetch(`/agents/${modalAgent.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(form),
          });
          if (!res.ok) throw new Error(await res.text());
        } else {
          // Create
          const res = await fetch("/agents/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(form),
          });
          if (!res.ok) throw new Error(await res.text());
        }
        setShowModal(false);
        fetchAgents();
      } catch (e: any) {
        setError(e.message || "Failed to save agent.");
      }
      setSubmitting(false);
    };

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
        <form
          className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md space-y-4"
          onSubmit={handleSubmit}
        >
          <h3 className="text-xl font-bold">
            {modalAgent ? "Edit Agent" : "Create New Agent"}
          </h3>
          <div>
            <label className="block text-sm font-medium">Name</label>
            <input
              className="w-full border rounded px-2 py-1"
              value={form.name || ""}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              onBlur={validate}
              required
            />
            {!valid && (
              <span className="text-xs text-red-600">Name must be unique.</span>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium">Description</label>
            <input
              className="w-full border rounded px-2 py-1"
              value={form.description || ""}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium">Type</label>
            <input
              className="w-full border rounded px-2 py-1"
              value={form.type || ""}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              required
            />
          </div>
          <div className="flex space-x-2">
            <Button type="button" variant="outline" onClick={testAgent}>
              Test
            </Button>
            {testResult && <span className="text-xs">{testResult}</span>}
          </div>
          <div className="flex space-x-2">
            <Button type="submit" disabled={submitting || !valid}>
              {modalAgent ? "Update" : "Create"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowModal(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    );
  };

  // Real-time status polling (optional, for demo use effect)
  useEffect(() => {
    const interval = setInterval(fetchAgents, 10000);
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Agent Registry</h2>
        <Button onClick={openCreateModal}>Create New Agent</Button>
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
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(0);
                }}
              />
            </div>
            <select
              className="rounded-md border border-input bg-background px-3 py-2"
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value as any);
                setPage(0);
              }}
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selected.size > 0 && (
        <div className="flex space-x-2">
          <Button onClick={() => handleBulkAction("activate")}>Activate</Button>
          <Button onClick={() => handleBulkAction("deactivate")}>
            Deactivate
          </Button>
          <Button
            onClick={() => handleBulkAction("delete")}
            variant="destructive"
          >
            Delete
          </Button>
          <Button onClick={clearSelection} variant="outline">
            Clear Selection
          </Button>
        </div>
      )}

      {/* Agent List */}
      <Card>
        <CardHeader>
          <CardTitle>Agents</CardTitle>
          <CardDescription>
            {loading ? "Loading..." : `${agents.length} agents found`}
            {error && <span className="text-red-600 ml-2">{error}</span>}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {agents.length === 0 && !loading ? (
              <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">No agents found</p>
              </div>
            ) : (
              <div className="rounded-md border">
                <div className="grid grid-cols-13 gap-4 border-b bg-muted/50 p-4 font-medium">
                  <div className="col-span-1">
                    <input
                      type="checkbox"
                      checked={selected.size === agents.length}
                      onChange={
                        selected.size === agents.length
                          ? clearSelection
                          : selectAll
                      }
                    />
                  </div>
                  <div className="col-span-3">Name</div>
                  <div className="col-span-2">Type</div>
                  <div className="col-span-2">Status</div>
                  <div className="col-span-2">Last Active</div>
                  <div className="col-span-3">Actions</div>
                </div>
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="grid grid-cols-13 gap-4 border-b p-4 last:border-0"
                  >
                    <div className="col-span-1 flex items-center">
                      <input
                        type="checkbox"
                        checked={selected.has(agent.id)}
                        onChange={() => toggleSelect(agent.id)}
                      />
                    </div>
                    <div className="col-span-3">
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
                      {agent.last_active}
                    </div>
                    <div className="col-span-3 flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditModal(agent)}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          setLoading(true);
                          await fetch(`/agents/${agent.id}`, {
                            method: "DELETE",
                          });
                          fetchAgents();
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {/* Pagination */}
          <div className="flex justify-end mt-4 space-x-2">
            <Button
              variant="outline"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              disabled={agents.length < PAGE_SIZE}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Analytics and Stats (unchanged, can be improved later) */}
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

      {/* Agent Stats (unchanged) */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agents.length}</div>
            <p className="text-xs text-muted-foreground">+2 from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
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
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agents.reduce((sum, agent) => sum + agent.conversations, 0)}
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
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agents.length
                ? (
                    agents.reduce(
                      (sum, agent) =>
                        sum + parseFloat(agent.avg_response_time || "0"),
                      0,
                    ) / agents.length
                  ).toFixed(2) + "s"
                : "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              -0.3s from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Creation/Edit Modal */}
      {showModal && <AgentModal />}
    </div>
  );
};

export default AgentRegistry;
