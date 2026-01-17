from langchain.messages import HumanMessage
from langchain_core.messages import ChatMessage
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3")

messages = [
    ChatMessage(role="control", content="thinking"),
    HumanMessage(input("Ask your math question: ")),
]

response = llm.invoke(messages)
print(response.content)