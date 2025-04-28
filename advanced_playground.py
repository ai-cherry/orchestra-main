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

# Run the app when this file is executed
if __name__ == "__main__":
    print("Starting Advanced Phidata Dashboard on http://localhost:7777")
    serve_playground_app("advanced_playground:app", reload=True)
