from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.ui import Console
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor
from pathlib import Path

# Define the model configuration for Ollama with model_info
model_client = OpenAIChatCompletionClient(
    model="qwen2.5",
    api_key="ollama",  # Ollama doesn't require a real API key
    base_url='http://localhost:11434/v1',  # Ollama's OpenAI-compatible endpoint
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": "unknown",
        "structured_output": False,  # Added to suppress warning
    }
)

# Setting up the code executor using Docker
workdir = Path("coding")
workdir.mkdir(exist_ok=True)
code_executor = DockerCommandLineCodeExecutor(work_dir=workdir)

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

# The AssistantAgent that writes code
assistant_agent = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    system_message=system_message,
)

# The code executor agent - uses CodeExecutorAgent, not AssistantAgent
executor_agent = CodeExecutorAgent(
    name="Executor",
    code_executor=code_executor,
)

# Set up termination condition
termination = TextMentionTermination("FINISH")

# Create a team with the agents
team = RoundRobinGroupChat(
    [assistant_agent, executor_agent],
    termination_condition=termination,
)

# Run the conversation
async def main():
    task = "Write a Python script that calculates the factorial of 5 and prints the result."
    await Console(team.run_stream(task=task))

# If running as a regular Python script:
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())