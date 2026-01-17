import autogen
from click import group

from AIOllama import user_proxy
from app1 import system_message

config_list = [{
    "model" : "qwen2.5",
    "base_url" : "http://localhost:11434/v1",
    "api_key" : "ollama"
}]
llm_config = {
    "config_list" : config_list,
    "temperature" : 0.7
}

code = autogen.AssistantAgent(
    name = "Coder",
    llm_config=llm_config,
    system_message = "You are an expert python coder."
)

reviewer = autogen.AssistantAgent(
    name = "Reviewer",
    llm_config=llm_config,
    system_message="You review code for bugs and improvements."
)

user_proxy = autogen.UserProxyAgent(
    name = "Proxy",
    human_input_mode= "TERMINATE",
    max_consecutive_auto_reply= 5,
    code_execution_config = {
        "work_dir" : "coding",
        "use_docker" : False
    },
)

groupchat = autogen.GroupChat(
    agents = [user_proxy,code,reviewer],
    messages = [],
    max_round= 2
)

manager = autogen.GroupChatManager(groupchat = groupchat, llm_config=llm_config)
user_proxy.initiate_chat(manager,
                         message="Create a function to sort a list using quicksortcd.")