from praisonaiagents import Agent, PraisonAIAgents
import os

from win32comext.shell.demos.servers.folder_view import tasks

# Set up MCP server command
filesystem_mcp_server_command = "npx @modelcontextprotocol/server-filesystem"
workingDirectory = os.path.abspath("D:/AI_Practice/Vikas_Rathod_Automation_Test_Engineer.pdf")

# Create agent with MCP - pass the command directly as a string to tools
file_agent = Agent(
    name="file_agent",
    role="File Manager",
    goal="Manage files in the working directory",
    instructions="You are a helpful AI agent that can read and write files in the working directory.",
    llm="ollama/llama2",
    tools=[f"mcp:{filesystem_mcp_server_command} {workingDirectory}"]
)

# Create agents instance and run
agents = PraisonAIAgents(
    agents=[file_agent],
    process="sequential"
)

# Run the task
response = agents.run(tasks="read content of file from local directory and analyse this resume is perfect for applying to test engineer postion or not?")
print(response)