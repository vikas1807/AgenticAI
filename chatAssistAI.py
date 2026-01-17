from click import prompt
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM

# Initialize the Ollama LLM
# Ensure the model (e.g., "llama3") is pulled and the Ollama service is running
llm = Ollama(model="llama3")

# Define a simple prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer the user's questions to the best of your ability."),
    ("human", "{question}")
])

# Create the LangChain pipeline (chain)
# This connects the prompt, model, and an output parser
chain = prompt | llm | StrOutputParser()

# Invoke the chain with a question
question = input("Ask your question: ")
response = chain.invoke({"question": question})

print(response)
