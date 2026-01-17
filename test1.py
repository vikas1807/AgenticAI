from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from pathlib import Path
import httpx

# Ollama configuration
OLLAMA_BASE_URL = 'http://localhost:11434'  # Change if Ollama is on a different machine

# Test connection first
print(f"Testing connection to {OLLAMA_BASE_URL}...")
try:
    import requests

    response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
    models = [m['name'] for m in response.json()['models']]
    print(f"✓ Connected! Available models: {models}")
    if 'qwen2.5' not in ' '.join(models):
        print("⚠ Warning: qwen2.5 not found. Run 'ollama pull qwen2.5' to install it.")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("Make sure Ollama is running: 'ollama serve'")
    exit(1)

# Define the model configuration for Ollama
model_client = OpenAIChatCompletionClient(
    model="qwen2.5",
    api_key="ollama",
    base_url=f"{OLLAMA_BASE_URL}/v1",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False,
    },
    timeout=httpx.Timeout(300.0, connect=60.0),
)

# Setting up the code executor using Docker
workdir = Path("coding")
workdir.mkdir(exist_ok=True)

try:
    code_executor = DockerCommandLineCodeExecutor(work_dir=workdir)
    print("✓ Docker executor initialized")
except Exception as e:
    print(f"✗ Docker failed: {e}")
    print("Make sure Docker Desktop is running")
    exit(1)

# System message for the assistant
system_message = """You are a helpful AI assistant who writes code and the user
executes it. Solve tasks using your python coding skills.
In the following cases, suggest python code (in a python coding block) for the
user to execute. When using code, you must indicate the script type in the code block.
You only need to create one working sample.
Do not suggest incomplete code which requires users to modify it.
Don't use a code block if it's not intended to be executed by the user. Don't
include multiple code blocks in one response. Do not ask users to copy and
paste the result. Instead, use 'print' function for the output when relevant.
Check the execution result returned by the user.

If the result indicates there is an error, fix the error.

IMPORTANT: If it has executed successfully, ONLY output 'FINISH'."""

# Create the AssistantAgent that writes code
assistant_agent = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    system_message=system_message,
)

# Create the CodeExecutorAgent that executes code
executor_agent = CodeExecutorAgent(
    name="Executor",
    code_executor=code_executor,
)

# Set up termination condition
termination = TextMentionTermination("FINISH")

# Create a team with round-robin communication
team = RoundRobinGroupChat(
    [assistant_agent, executor_agent],
    termination_condition=termination,
    max_turns=10,
)


# Run the conversation
async def main():
    # Define the task
    task = input("Enter your task: ")

    print(f"\n{'=' * 60}")
    print(f"Starting Task: {task}")
    print(f"{'=' * 60}\n")

    try:
        # Run the team with the task
        await Console(team.run_stream(task=task))
        print("\n✓ Task completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())