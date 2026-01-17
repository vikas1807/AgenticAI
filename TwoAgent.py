from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
from autogen_ext.code_executors import DockerCommandLineCodeExecutor

# Define the model configuration
config_list = [
    {
        # Let's choose the Meta's Llama 3.1 model (model names must match Ollama exactly)
        "model": "qwen2.5",
        # We specify the API Type as 'ollama' so it uses the Ollama client class
        "api_type": "ollama",
        "stream": False,
        "client_host": "http://localhost:11434/v1/",
    }
]

from pathlib import Path

# Setting up the code executor using Docker
workdir = Path("coding")
workdir.mkdir(exist_ok=True)
code_executor = DockerCommandLineCodeExecutor(work_dir=str(workdir))

# Setting up the agents

# The UserProxyAgent will execute the code that the AssistantAgent provides
user_proxy_agent = UserProxyAgent(
    name="User",
)

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

# The AssistantAgent, using the Ollama config, will take the coding request and return code
assistant_agent = AssistantAgent(
    name="Ollama_Assistant",
    system_message=system_message,
    model_client=config_list[0]  # Pass the model configuration to the assistant agent
)

# Example interaction
user_proxy_agent.init_conversation(assistant_agent)
