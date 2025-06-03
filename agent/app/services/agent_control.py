def get_agent_logs(agent_id: str):
    """Fetch logs for the agent."""
    return {"logs": [f"Log for agent {agent_id} line 1", f"Log for agent {agent_id} line 2"]}

def restart_agent(agent_id: str):
    """Restart the agent process (stub)."""
    return {"status": "success", "message": f"Agent {agent_id} restarted."}

def get_agent_config(agent_id: str):
    """Fetch agent config (stub)."""
    return {"config": {"param": "value"}}

def update_agent_config(agent_id: str, config: dict):
    """Update agent config (stub)."""
    return {"status": "success", "config": config}

def get_agent_metrics(agent_id: str):
    """Fetch real-time metrics for the agent (stub)."""
    return {"cpu": 10.5, "mem": 123.4}
