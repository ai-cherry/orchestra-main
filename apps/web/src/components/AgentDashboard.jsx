import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  PlayArrow as TestIcon,
} from "@mui/icons-material";
import { useSnackbar } from "notistack";
import AgentForm from "./AgentForm";
import AgentCard from "./AgentCard";
import ConversationHistory from "./ConversationHistory";
import AgentMetrics from "./AgentMetrics";

// API service for agent operations
import {
  getAgents,
  getAgentById,
  createAgent,
  updateAgent,
  deleteAgent,
  testAgent,
  getAgentConversations,
} from "../services/agentService";

/**
 * Agent Dashboard component for managing AI Orchestra agents
 *
 * This component provides a UI for viewing, creating, editing, testing,
 * and monitoring agents in the AI Orchestra system.
 */
const AgentDashboard = () => {
  // State
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState("create");
  const [tabValue, setTabValue] = useState(0);
  const [testInput, setTestInput] = useState("");
  const [testResponse, setTestResponse] = useState("");
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Snackbar for notifications
  const { enqueueSnackbar } = useSnackbar();

  // Fetch agents on component mount
  useEffect(() => {
    fetchAgents();
  }, []);

  // Fetch conversations when an agent is selected
  useEffect(() => {
    if (selectedAgent) {
      fetchConversations(selectedAgent.id);
    }
  }, [selectedAgent]);

  // Fetch agents from API
  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await getAgents();
      setAgents(response.agents);

      // Select the first agent if none is selected
      if (response.agents.length > 0 && !selectedAgent) {
        setSelectedAgent(response.agents[0]);
      }
    } catch (error) {
      console.error("Error fetching agents:", error);
      enqueueSnackbar("Failed to fetch agents", { variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  // Fetch conversations for an agent
  const fetchConversations = async (agentId) => {
    try {
      const response = await getAgentConversations(agentId);
      setConversations(response.conversations);
    } catch (error) {
      console.error("Error fetching conversations:", error);
      enqueueSnackbar("Failed to fetch conversations", { variant: "error" });
    }
  };

  // Handle agent selection
  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    setTabValue(0);
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Open create agent form
  const handleCreateAgent = () => {
    setFormMode("create");
    setFormOpen(true);
  };

  // Open edit agent form
  const handleEditAgent = () => {
    setFormMode("edit");
    setFormOpen(true);
  };

  // Open delete confirmation dialog
  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  // Delete agent
  const handleDeleteConfirm = async () => {
    try {
      await deleteAgent(selectedAgent.id);
      enqueueSnackbar("Agent deleted successfully", { variant: "success" });

      // Remove agent from state
      setAgents(agents.filter((agent) => agent.id !== selectedAgent.id));

      // Select another agent if available
      if (agents.length > 1) {
        const newSelectedAgent = agents.find(
          (agent) => agent.id !== selectedAgent.id,
        );
        setSelectedAgent(newSelectedAgent);
      } else {
        setSelectedAgent(null);
      }

      setDeleteDialogOpen(false);
    } catch (error) {
      console.error("Error deleting agent:", error);
      enqueueSnackbar("Failed to delete agent", { variant: "error" });
    }
  };

  // Close delete confirmation dialog
  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  // Open test dialog
  const handleTestClick = () => {
    setTestInput("");
    setTestResponse("");
    setTestDialogOpen(true);
  };

  // Run agent test
  const handleTestRun = async () => {
    if (!testInput.trim()) {
      enqueueSnackbar("Please enter test input", { variant: "warning" });
      return;
    }

    setTestLoading(true);
    try {
      const response = await testAgent(selectedAgent.id, { text: testInput });
      setTestResponse(response.response);
    } catch (error) {
      console.error("Error testing agent:", error);
      enqueueSnackbar("Failed to test agent", { variant: "error" });
    } finally {
      setTestLoading(false);
    }
  };

  // Close test dialog
  const handleTestClose = () => {
    setTestDialogOpen(false);
  };

  // Handle form submission
  const handleFormSubmit = async (agentData) => {
    try {
      if (formMode === "create") {
        // Create new agent
        const response = await createAgent(agentData);
        enqueueSnackbar("Agent created successfully", { variant: "success" });

        // Add new agent to state
        const newAgent = {
          id: response.id,
          name: response.name,
          description: response.description,
          status: response.status,
        };

        setAgents([...agents, newAgent]);
        setSelectedAgent(newAgent);
      } else {
        // Update existing agent
        const response = await updateAgent(selectedAgent.id, agentData);
        enqueueSnackbar("Agent updated successfully", { variant: "success" });

        // Update agent in state
        const updatedAgents = agents.map((agent) =>
          agent.id === selectedAgent.id
            ? {
                ...agent,
                name: response.name,
                description: response.description,
              }
            : agent,
        );

        setAgents(updatedAgents);
        setSelectedAgent({
          ...selectedAgent,
          name: response.name,
          description: response.description,
        });
      }

      setFormOpen(false);
    } catch (error) {
      console.error("Error saving agent:", error);
      enqueueSnackbar("Failed to save agent", { variant: "error" });
    }
  };

  // Close form dialog
  const handleFormClose = () => {
    setFormOpen(false);
  };

  // Render loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="60vh"
        >
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Agent Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Agent List */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 2, height: "100%" }}>
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              mb={2}
            >
              <Typography variant="h6">Agents</Typography>
              <Box>
                <IconButton
                  onClick={fetchAgents}
                  size="small"
                  title="Refresh agents"
                >
                  <RefreshIcon />
                </IconButton>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={handleCreateAgent}
                  size="small"
                >
                  New Agent
                </Button>
              </Box>
            </Box>

            <Divider sx={{ mb: 2 }} />

            {agents.length === 0 ? (
              <Typography
                variant="body2"
                color="textSecondary"
                align="center"
                sx={{ py: 4 }}
              >
                No agents found. Create your first agent to get started.
              </Typography>
            ) : (
              <Box sx={{ maxHeight: "60vh", overflow: "auto" }}>
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    selected={selectedAgent && selectedAgent.id === agent.id}
                    onClick={() => handleAgentSelect(agent)}
                  />
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Agent Details */}
        <Grid item xs={12} md={8}>
          {selectedAgent ? (
            <Paper elevation={2} sx={{ p: 2 }}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={2}
              >
                <Typography variant="h6">{selectedAgent.name}</Typography>
                <Box>
                  <IconButton onClick={handleTestClick} title="Test agent">
                    <TestIcon />
                  </IconButton>
                  <IconButton onClick={handleEditAgent} title="Edit agent">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={handleDeleteClick} title="Delete agent">
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </Box>

              <Typography variant="body2" color="textSecondary" paragraph>
                {selectedAgent.description}
              </Typography>

              <Divider sx={{ mb: 2 }} />

              <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
                <Tabs value={tabValue} onChange={handleTabChange}>
                  <Tab label="Conversations" />
                  <Tab label="Metrics" />
                  <Tab label="Configuration" />
                </Tabs>
              </Box>

              {/* Tab Panels */}
              <Box sx={{ py: 2 }}>
                {tabValue === 0 && (
                  <ConversationHistory
                    conversations={conversations}
                    agentId={selectedAgent.id}
                    onRefresh={() => fetchConversations(selectedAgent.id)}
                  />
                )}

                {tabValue === 1 && <AgentMetrics agentId={selectedAgent.id} />}

                {tabValue === 2 && (
                  <Box>
                    <Typography variant="subtitle1">
                      Agent Configuration
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Edit the agent to modify its configuration.
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          ) : (
            <Paper elevation={2} sx={{ p: 4, textAlign: "center" }}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                No Agent Selected
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Select an agent from the list or create a new one to get
                started.
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={<AddIcon />}
                onClick={handleCreateAgent}
              >
                Create Agent
              </Button>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Agent Form Dialog */}
      <Dialog open={formOpen} onClose={handleFormClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {formMode === "create" ? "Create New Agent" : "Edit Agent"}
        </DialogTitle>
        <DialogContent>
          <AgentForm
            mode={formMode}
            initialData={formMode === "edit" ? selectedAgent : null}
            onSubmit={handleFormSubmit}
            onCancel={handleFormClose}
          />
        </DialogContent>
      </Dialog>

      {/* Test Dialog */}
      <Dialog
        open={testDialogOpen}
        onClose={handleTestClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Test Agent: {selectedAgent?.name}</DialogTitle>
        <DialogContent>
          <TextField
            label="Test Input"
            multiline
            rows={4}
            fullWidth
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            margin="normal"
            variant="outlined"
            placeholder="Enter text to test the agent..."
          />

          {testLoading && (
            <Box display="flex" justifyContent="center" my={2}>
              <CircularProgress size={24} />
            </Box>
          )}

          {testResponse && (
            <Card variant="outlined" sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" gutterBottom>
                  Agent Response:
                </Typography>
                <Typography variant="body2">{testResponse}</Typography>
              </CardContent>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTestClose}>Close</Button>
          <Button
            onClick={handleTestRun}
            variant="contained"
            color="primary"
            disabled={testLoading || !testInput.trim()}
          >
            Run Test
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={handleDeleteCancel}>
        <DialogTitle>Delete Agent</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the agent "{selectedAgent?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AgentDashboard;
