from praisonaiagents import Agent, PraisonAIAgents
from praisonaiagents.main import MCP
import os

# Configure Ollama via environment variables
os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"
os.environ["OPENAI_MODEL_NAME"] = "llama3.2"
os.environ["OPENAI_API_KEY"] = "ollama"  # Dummy key for Ollama

# Set up MCP server command
filesystem_mcp_server_command = "npx @modelcontextprotocol/server-filesystem"
workingDirectory = os.getcwd()

# Create MCP instance
mcp_server = MCP(server_params=f"{filesystem_mcp_server_command} {workingDirectory}")

# Create agent WITHOUT llm parameter - it will use env vars
file_agent = Agent(
    name="file_agent",
    role="File Manager",
    goal="Manage files in the working directory",
    instructions="You are a helpful AI agent that can read and write files in the working directory.",
    tools=[mcp_server]
    # No llm parameter here!
)

# Create agents instance and run
agents = PraisonAIAgents(
    agents=[file_agent],
    process="sequential"
)

# Run the task
response = agents.start("Create a python file that prints 'Hello, World!' and then read the file content")
print(response)