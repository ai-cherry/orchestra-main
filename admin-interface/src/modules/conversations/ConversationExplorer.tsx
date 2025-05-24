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
import { LineChart } from "../../components/ui/charts";
import { formatNumber } from "../../lib/utils";

/**
 * Conversation Explorer component that provides access to conversation history
 */
const ConversationExplorer = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState<
    "today" | "7days" | "30days" | "all"
  >("7days");
  const [selectedConversation, setSelectedConversation] = useState<
    string | null
  >(null);

  // Sample conversation data
  const conversations = [
    {
      id: "conv-001",
      agentName: "Content Creator",
      agentId: "agent-001",
      userId: "user-123",
      startTime: "2025-05-10T14:30:00Z",
      endTime: "2025-05-10T14:45:00Z",
      duration: "15 minutes",
      messageCount: 12,
      status: "completed",
      summary: "Discussion about creating content for a blog post on AI trends",
      lastMessage:
        "Thanks for the detailed outline. I'll start working on the draft.",
    },
    {
      id: "conv-002",
      agentName: "Research Assistant",
      agentId: "agent-002",
      userId: "user-456",
      startTime: "2025-05-10T10:15:00Z",
      endTime: "2025-05-10T10:45:00Z",
      duration: "30 minutes",
      messageCount: 24,
      status: "completed",
      summary: "Research on quantum computing advancements in 2025",
      lastMessage:
        "I've compiled all the research papers you requested. Would you like me to summarize the key findings?",
    },
    {
      id: "conv-003",
      agentName: "Data Analyst",
      agentId: "agent-003",
      userId: "user-789",
      startTime: "2025-05-10T09:00:00Z",
      endTime: "2025-05-10T09:20:00Z",
      duration: "20 minutes",
      messageCount: 15,
      status: "completed",
      summary: "Analysis of quarterly sales data and trend identification",
      lastMessage:
        "Based on the data, I've identified three key trends that could help improve next quarter's performance.",
    },
    {
      id: "conv-004",
      agentName: "Project Manager",
      agentId: "agent-004",
      userId: "user-123",
      startTime: "2025-05-09T16:00:00Z",
      endTime: "2025-05-09T16:30:00Z",
      duration: "30 minutes",
      messageCount: 22,
      status: "completed",
      summary: "Project planning for Q3 marketing campaign",
      lastMessage:
        "I've created the project timeline with all the milestones we discussed. I'll share it with the team.",
    },
    {
      id: "conv-005",
      agentName: "Creative Writer",
      agentId: "agent-005",
      userId: "user-456",
      startTime: "2025-05-09T13:45:00Z",
      endTime: "2025-05-09T14:15:00Z",
      duration: "30 minutes",
      messageCount: 18,
      status: "completed",
      summary: "Brainstorming session for new product names",
      lastMessage:
        "These are some great options! I'll present them to the marketing team tomorrow.",
    },
    {
      id: "conv-006",
      agentName: "Customer Support",
      agentId: "agent-006",
      userId: "user-789",
      startTime: "2025-05-08T11:30:00Z",
      endTime: "2025-05-08T11:45:00Z",
      duration: "15 minutes",
      messageCount: 10,
      status: "completed",
      summary: "Troubleshooting account access issues",
      lastMessage:
        "Perfect! I can access my account now. Thank you for your help!",
    },
  ];

  // Filter conversations based on search query and date range
  const filteredConversations = conversations.filter((conversation) => {
    const matchesSearch =
      conversation.agentName
        .toLowerCase()
        .includes(searchQuery.toLowerCase()) ||
      conversation.summary.toLowerCase().includes(searchQuery.toLowerCase());

    // Date filtering logic would go here in a real implementation
    // For now, we'll just return true for all date ranges
    const matchesDate = true;

    return matchesSearch && matchesDate;
  });

  // Get the selected conversation details
  const conversationDetails = selectedConversation
    ? conversations.find((c) => c.id === selectedConversation)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">
          Conversation Explorer
        </h2>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col space-y-4 md:flex-row md:space-x-4 md:space-y-0">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search conversations..."
                className="w-full rounded-md border border-input bg-background px-3 py-2"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              className="rounded-md border border-input bg-background px-3 py-2"
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as any)}
            >
              <option value="today">Today</option>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Conversation List */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Conversations</CardTitle>
            <CardDescription>
              {filteredConversations.length} conversations found
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredConversations.length === 0 ? (
                <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed">
                  <p className="text-sm text-muted-foreground">
                    No conversations found
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`cursor-pointer rounded-md border p-4 transition-colors hover:bg-muted/50 ${
                        selectedConversation === conversation.id
                          ? "border-primary bg-muted/50"
                          : ""
                      }`}
                      onClick={() => setSelectedConversation(conversation.id)}
                    >
                      <div className="flex justify-between">
                        <div className="font-medium">
                          {conversation.agentName}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {new Date(
                            conversation.startTime,
                          ).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="mt-1 text-sm text-muted-foreground">
                        {conversation.summary}
                      </div>
                      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                        <div>{conversation.duration}</div>
                        <div>{conversation.messageCount} messages</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Conversation Details */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Conversation Details</CardTitle>
            <CardDescription>
              {conversationDetails
                ? `Conversation with ${conversationDetails.agentName}`
                : "Select a conversation to view details"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!conversationDetails ? (
              <div className="flex h-[300px] items-center justify-center rounded-md border border-dashed">
                <p className="text-sm text-muted-foreground">
                  No conversation selected
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium">Agent</div>
                    <div className="text-sm text-muted-foreground">
                      {conversationDetails.agentName}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">User ID</div>
                    <div className="text-sm text-muted-foreground">
                      {conversationDetails.userId}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">Start Time</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(conversationDetails.startTime).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">End Time</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(conversationDetails.endTime).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">Duration</div>
                    <div className="text-sm text-muted-foreground">
                      {conversationDetails.duration}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">Messages</div>
                    <div className="text-sm text-muted-foreground">
                      {conversationDetails.messageCount}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-sm font-medium">Summary</div>
                  <div className="text-sm text-muted-foreground">
                    {conversationDetails.summary}
                  </div>
                </div>

                <div>
                  <div className="text-sm font-medium">Last Message</div>
                  <div className="text-sm text-muted-foreground">
                    {conversationDetails.lastMessage}
                  </div>
                </div>

                <div className="pt-4">
                  <Button variant="outline" size="sm">
                    View Full Conversation
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Conversation Analytics */}
      <Tabs defaultValue="volume" className="space-y-4">
        <TabsList>
          <TabsTrigger value="volume">Conversation Volume</TabsTrigger>
          <TabsTrigger value="duration">Duration</TabsTrigger>
          <TabsTrigger value="agents">By Agent</TabsTrigger>
        </TabsList>
        <TabsContent value="volume" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversation Volume</CardTitle>
              <CardDescription>
                Number of conversations over time
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "May 1", value: 45 },
                  { name: "May 2", value: 52 },
                  { name: "May 3", value: 48 },
                  { name: "May 4", value: 61 },
                  { name: "May 5", value: 55 },
                  { name: "May 6", value: 67 },
                  { name: "May 7", value: 62 },
                  { name: "May 8", value: 70 },
                  { name: "May 9", value: 75 },
                  { name: "May 10", value: 68 },
                ]}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="duration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversation Duration</CardTitle>
              <CardDescription>
                Average conversation duration by day
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <LineChart
                data={[
                  { name: "May 1", value: 12 },
                  { name: "May 2", value: 15 },
                  { name: "May 3", value: 18 },
                  { name: "May 4", value: 14 },
                  { name: "May 5", value: 16 },
                  { name: "May 6", value: 19 },
                  { name: "May 7", value: 17 },
                  { name: "May 8", value: 15 },
                  { name: "May 9", value: 20 },
                  { name: "May 10", value: 18 },
                ]}
                xAxisKey="name"
                yAxisKey="value"
                className="h-[300px]"
              />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="agents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Conversations by Agent</CardTitle>
              <CardDescription>
                Distribution of conversations by agent
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { agent: "Content Creator", count: 245, percentage: 28 },
                  { agent: "Research Assistant", count: 187, percentage: 21 },
                  { agent: "Data Analyst", count: 156, percentage: 18 },
                  { agent: "Project Manager", count: 132, percentage: 15 },
                  { agent: "Creative Writer", count: 98, percentage: 11 },
                  { agent: "Customer Support", count: 62, percentage: 7 },
                ].map((item) => (
                  <div key={item.agent} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <span className="text-sm font-medium">
                          {item.agent}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-muted-foreground">
                          {item.count}
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
    </div>
  );
};

export default ConversationExplorer;
