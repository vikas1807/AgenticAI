from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
import httpx

# Model configuration
model_client = OpenAIChatCompletionClient(
    model="qwen2.5",
    api_key="ollama",
    base_url="http://localhost:11434/v1/",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False,
    },
    timeout=httpx.Timeout(300.0, connect=60.0),
)

# Create a simple assistant
assistant = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    system_message="You are a helpful AI assistant. Answer questions clearly and concisely.",
)

# Create a team with just the assistant
team = RoundRobinGroupChat(
    [assistant],
    termination_condition=MaxMessageTermination(5),
)

# Run
async def main():
    await Console(team.run_stream(task="Hi Can you pls create a program for factorial number in python."))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())