import time

import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By
import json


class AdvancedOllamaAgent:
    def __init__(self, model="qwen2.5"):
        self.model = model
        self.driver = None
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "navigate_browser",
                    "description": "Navigate to a specific URL in the browser",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to navigate to"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web using Google",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def launch_browser(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        print("✅ Browser launched!")

    def navigate_browser(self, url):
        if not url.startswith('http'):
            url = 'https://' + url
        self.driver.get(url)
        return {"status": "success", "message": f"Navigated to {url}"}

    def search_web(self, query):
        self.driver.get("https://www.google.com")
        search_box = self.driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.submit()
        return {"status": "success", "message": f"Searched for: {query}"}

    def run_agent(self, task):
        """Run the agent with function calling"""
        messages = [{"role": "user", "content": task}]

        response = ollama.chat(
            model=self.model,
            messages=messages,
            tools=self.tools
        )

        # Check if the model wants to call a function
        if response['message'].get('tool_calls'):
            for tool_call in response['message']['tool_calls']:
                function_name = tool_call['function']['name']
                arguments = tool_call['function']['arguments']

                print(f"🔧 Calling function: {function_name}")
                print(f"📋 Arguments: {arguments}")

                # Execute the function
                if function_name == "navigate_browser":
                    result = self.navigate_browser(arguments['url'])
                elif function_name == "search_web":
                    result = self.search_web(arguments['query'])

                print(f"✅ Result: {result}")
        else:
            print(f"🤖 Response: {response['message']['content']}")

    def close_browser(self):
        if self.driver:
            self.driver.quit()


# Example usage
if __name__ == "__main__":
    agent = AdvancedOllamaAgent(model="qwen2.5")
    agent.launch_browser()

    agent.run_agent("Go to github.com")
    time.sleep(3)

    agent.run_agent("Search for 'Python AI tutorials'")
    time.sleep(3)

    agent.close_browser()