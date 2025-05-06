from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.wikipedia import Wikipedia
from phi.tools.calculator import Calculator
from phi.playground import Playground, serve_playground_app

# Create a Web Search Agent
web_agent = Agent(
    name="Web Search Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    instructions=[
        "You are a helpful web search assistant.",
        "Always include sources in your responses.",
        "Respond in a concise and informative manner."
    ],
    storage=SqlAgentStorage(table_name="web_agent", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True,
)

# Create a Research Agent with Wikipedia
research_agent = Agent(
    name="Research Assistant",
    model=OpenAIChat(id="gpt-4o"),
    tools=[Wikipedia()],
    instructions=[
        "You are a knowledgeable research assistant.",
        "Use Wikipedia to provide detailed information on topics.",
        "Always cite your sources properly.",
        "Format your responses in a scholarly style."
    ],
    storage=SqlAgentStorage(table_name="research_agent", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True,
)

# Create a Math Agent with Calculator
math_agent = Agent(
    name="Math Helper",
    model=OpenAIChat(id="gpt-4o"),
    tools=[Calculator()],
    instructions=[
        "You are a math assistant who helps with calculations.",
        "Show your work step by step.",
        "Explain mathematical concepts clearly."
    ],
    storage=SqlAgentStorage(table_name="math_agent", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True,
)

# Create the Playground with multiple agents
app = Playground(
    agents=[web_agent, research_agent, math_agent],
    title="Advanced Agent Dashboard",
    description="A dashboard with multiple specialized agents for different tasks."
).get_app()

class DynamicAgentScaler:
    """
    Handles dynamic scaling of agents based on load and performance metrics.
    """

    def __init__(self, min_agents=1, max_agents=10, scale_up_threshold=75, scale_down_threshold=30):
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.current_agents = min_agents

    def get_current_load(self):
        """Simulate fetching the current load percentage."""
        # Replace with actual logic to fetch load metrics
        import random
        return random.randint(10, 100)

    def scale_up(self):
        """Scale up the number of agents."""
        if self.current_agents < self.max_agents:
            self.current_agents += 1
            print(f"Scaled up to {self.current_agents} agents.")
        else:
            print("Maximum agents reached. Cannot scale up further.")

    def scale_down(self):
        """Scale down the number of agents."""
        if self.current_agents > self.min_agents:
            self.current_agents -= 1
            print(f"Scaled down to {self.current_agents} agents.")
        else:
            print("Minimum agents reached. Cannot scale down further.")

    def adjust_agents(self):
        """Adjust the number of agents based on the current load."""
        current_load = self.get_current_load()
        print(f"Current load: {current_load}%")

        if current_load > self.scale_up_threshold:
            self.scale_up()
        elif current_load < self.scale_down_threshold:
            self.scale_down()

class PredictiveRouter:
    """
    Implements predictive routing using a machine learning model.
    """

    def __init__(self, model_path="predictive_model.pkl"):
        self.model_path = model_path
        self.model = self.load_model()

    def load_model(self):
        """Load the predictive model from a file."""
        import pickle
        try:
            with open(self.model_path, "rb") as f:
                model = pickle.load(f)
            print("Predictive model loaded successfully.")
            return model
        except FileNotFoundError:
            print("Predictive model not found. Please train and save the model.")
            return None

    def predict_best_agent(self, request_features):
        """Predict the best agent for a given request."""
        if not self.model:
            print("No model available. Falling back to default routing.")
            return None

        try:
            prediction = self.model.predict([request_features])
            print(f"Predicted best agent: {prediction[0]}")
            return prediction[0]
        except Exception as e:
            print(f"Error during prediction: {e}")
            return None

class MultiRegionRouter:
    """
    Implements multi-region support for routing requests to agents.
    """

    def __init__(self, regions):
        """
        Initialize the router with available regions.

        Args:
            regions (dict): A dictionary mapping region names to agent lists.
        """
        self.regions = regions

    def get_nearest_region(self, user_location):
        """
        Determine the nearest region based on user location.

        Args:
            user_location (tuple): A tuple of (latitude, longitude).

        Returns:
            str: The name of the nearest region.
        """
        import geopy.distance

        nearest_region = None
        shortest_distance = float('inf')

        for region, region_location in self.regions.items():
            distance = geopy.distance.distance(user_location, region_location['location']).km
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_region = region

        print(f"Nearest region: {nearest_region} ({shortest_distance:.2f} km)")
        return nearest_region

    def route_request(self, user_location):
        """
        Route a request to the best agent in the nearest region.

        Args:
            user_location (tuple): A tuple of (latitude, longitude).

        Returns:
            str: The name of the selected agent.
        """
        nearest_region = self.get_nearest_region(user_location)
        if nearest_region and self.regions[nearest_region]['agents']:
            selected_agent = self.regions[nearest_region]['agents'][0]  # Simplified selection logic
            print(f"Routed to agent: {selected_agent} in region: {nearest_region}")
            return selected_agent
        else:
            print("No agents available in the nearest region.")
            return None

class CostPerformanceOptimizer:
    """
    Implements cost-aware routing with a 70% weight on performance and 30% on cost.
    """

    def __init__(self, agents):
        """
        Initialize the optimizer with agent data.

        Args:
            agents (list): A list of dictionaries containing agent data with 'performance' and 'cost'.
        """
        self.agents = agents

    def calculate_score(self, agent):
        """
        Calculate the weighted score for an agent.

        Args:
            agent (dict): A dictionary containing 'performance' and 'cost'.

        Returns:
            float: The weighted score.
        """
        performance_weight = 0.7
        cost_weight = 0.3
        return (agent['performance'] * performance_weight) - (agent['cost'] * cost_weight)

    def select_best_agent(self):
        """
        Select the best agent based on the weighted score.

        Returns:
            dict: The best agent.
        """
        best_agent = max(self.agents, key=self.calculate_score)
        print(f"Selected best agent: {best_agent['name']} with score: {self.calculate_score(best_agent):.2f}")
        return best_agent

class AgentHealthChecker:
    """
    Periodically checks the health of agents and removes unhealthy ones from the routing table.
    """

    def __init__(self, agents):
        """
        Initialize the health checker with a list of agents.

        Args:
            agents (list): A list of agent names.
        """
        self.agents = {agent: True for agent in agents}  # True indicates healthy

    def check_health(self, agent):
        """
        Simulate a health check for an agent.

        Args:
            agent (str): The name of the agent.

        Returns:
            bool: True if the agent is healthy, False otherwise.
        """
        import random
        return random.choice([True, False])  # Simulate health check with random outcome

    def perform_health_checks(self):
        """
        Perform health checks for all agents and update their status.
        """
        for agent in list(self.agents.keys()):
            is_healthy = self.check_health(agent)
            self.agents[agent] = is_healthy
            if not is_healthy:
                print(f"Agent {agent} is unhealthy and will be removed.")
                del self.agents[agent]
            else:
                print(f"Agent {agent} is healthy.")

class DebuggingTools:
    """
    Provides tools for debugging routing decisions and simulating scenarios.
    """

    def __init__(self):
        self.debug_mode = False

    def enable_debug_mode(self):
        """Enable detailed logging for debugging."""
        self.debug_mode = True
        print("Debug mode enabled.")

    def disable_debug_mode(self):
        """Disable detailed logging."""
        self.debug_mode = False
        print("Debug mode disabled.")

    def log_decision(self, decision_details):
        """Log detailed information about a routing decision."""
        if self.debug_mode:
            print(f"[DEBUG] Routing Decision: {decision_details}")

    def simulate_scenario(self, scenario_name, scenario_function):
        """Simulate a specific scenario for testing."""
        print(f"Simulating scenario: {scenario_name}")
        try:
            scenario_function()
            print(f"Scenario '{scenario_name}' completed successfully.")
        except Exception as e:
            print(f"Error during scenario '{scenario_name}': {e}")

# Run the app when this file is executed
if __name__ == "__main__":
    print("Starting Advanced Phidata Dashboard on http://localhost:7777")
    serve_playground_app("advanced_playground:app", reload=True)

    # Example usage of DynamicAgentScaler
    scaler = DynamicAgentScaler()

    # Simulate periodic scaling adjustments
    import time
    for _ in range(10):
        scaler.adjust_agents()
        time.sleep(2)

    # Example usage of PredictiveRouter
    predictive_router = PredictiveRouter()

    # Simulate a request with features
    sample_request = [0.8, 0.2, 0.5]  # Example feature vector
    best_agent = predictive_router.predict_best_agent(sample_request)
    print(f"Best agent for the request: {best_agent}")

    # Example usage of MultiRegionRouter
    regions = {
        "us-east": {"location": (37.7749, -122.4194), "agents": ["Agent A", "Agent B"]},
        "us-west": {"location": (40.7128, -74.0060), "agents": ["Agent C"]},
        "europe": {"location": (48.8566, 2.3522), "agents": ["Agent D", "Agent E"]},
    }

    multi_region_router = MultiRegionRouter(regions)

    # Simulate a user request from a specific location
    user_location = (34.0522, -118.2437)  # Los Angeles, CA
    selected_agent = multi_region_router.route_request(user_location)
    print(f"Selected agent: {selected_agent}")

    # Example usage of CostPerformanceOptimizer
    agents = [
        {"name": "Agent A", "performance": 85, "cost": 20},
        {"name": "Agent B", "performance": 75, "cost": 15},
        {"name": "Agent C", "performance": 90, "cost": 25},
    ]

    optimizer = CostPerformanceOptimizer(agents)
    best_agent = optimizer.select_best_agent()
    print(f"Best agent for cost-performance optimization: {best_agent['name']}")

    # Example usage of AgentHealthChecker
    health_checker = AgentHealthChecker(["Agent A", "Agent B", "Agent C"])

    # Simulate periodic health checks
    for _ in range(5):
        health_checker.perform_health_checks()
        print(f"Current healthy agents: {list(health_checker.agents.keys())}")
        time.sleep(3)

    # Example usage of DebuggingTools
    debugger = DebuggingTools()

    # Enable debug mode
    debugger.enable_debug_mode()

    # Log a sample decision
    debugger.log_decision({"agent": "Agent A", "reason": "High performance score"})

    # Simulate a scenario
    def sample_scenario():
        print("Executing sample scenario...")
        # Add scenario-specific logic here

    debugger.simulate_scenario("Sample Scenario", sample_scenario)
