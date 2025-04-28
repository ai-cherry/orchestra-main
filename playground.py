from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.storage.agent.sqlite import SqlAgentStorage
from phi.tools.duckduckgo import DuckDuckGo
from phi.playground import Playground, serve_playground_app

# Define a web agent with DuckDuckGo search capability
web_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    storage=SqlAgentStorage(table_name="web_agent", db_file="agents.db"),
    add_history_to_messages=True,
    markdown=True,
)

# Create the Playground app with our agent
app = Playground(agents=[web_agent]).get_app()

# Run the app when this file is executed
if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True)
