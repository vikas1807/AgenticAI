import autogen

config_list = [{
    "model":"qwen2.5",
    "base_url" : "http://localhost:11434/v1",
    "api_key" : "ollama"
}]
llm_config = {
    "config_list" : config_list,
    "temperature" : 0.7
}

assistant = autogen.AssistantAgent(
    name = "Assistant",
    llm_config = llm_config
)

user_proxy = autogen.UserProxyAgent(
    name = "UserProxy",
    human_input_mode = "ALWAYS",
    max_consecutive_auto_reply= 10,
    code_execution_config = {
        "work_dir" : "coding",
        "use_docker" : False,
    },
)

user_proxy.initiate_chat(
    assistant,
    message= "Hi Can you pls create a program for find repeated character in a string 'vikasrathod' in python?"

)
