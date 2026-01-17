import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time


class OllamaAIBrowserAgent:
    def __init__(self, model="llama2"):
        self.model = model
        self.driver = None
        self.conversation_history = []

    def launch_browser(self):
        """Launch Chrome browser"""
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        print("Browser launched successfully!")
        return self.driver

    def get_page_info(self):
        """Get current page information"""
        try:
            title = self.driver.title
            url = self.driver.current_url
            return f"Current page: {title}\nURL: {url}"
        except:
            return "No page loaded"

    def navigate_to_url(self, url):
        """Navigate to a specific URL"""
        if not url.startswith('http'):
            url = 'https://' + url
        self.driver.get(url)
        time.sleep(2)
        return f"Navigated to {url}"

    def search_google(self, query):
        """Perform Google search"""
        self.driver.get("https://www.amazon.in/")
        time.sleep(1)
        try:
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
            return f"Searched Google for: {query}"
        except Exception as e:
            return f"Search failed: {str(e)}"

    def click_element(self, text):
        """Click an element containing specific text"""
        try:
            element = self.driver.find_element(By.PARTIAL_LINK_TEXT, text)
            element.click()
            time.sleep(2)
            return f"Clicked on: {text}"
        except:
            return f"Could not find element with text: {text}"

    def get_page_text(self):
        """Get visible text from current page"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            text = body.text[:1000]  # Limit to first 1000 characters
            return text
        except:
            return "Could not retrieve page text"

    def take_screenshot(self, filename="screenshot.png"):
        """Take screenshot of current page"""
        self.driver.save_screenshot(filename)
        return f"Screenshot saved as {filename}"

    def execute_action(self, action_type, **kwargs):
        """Execute browser actions based on AI decision"""
        actions = {
            "navigate": lambda: self.navigate_to_url(kwargs.get('url', '')),
            "search": lambda: self.search_google(kwargs.get('query', '')),
            "click": lambda: self.click_element(kwargs.get('text', '')),
            "screenshot": lambda: self.take_screenshot(kwargs.get('filename', 'screenshot.png')),
            "get_text": lambda: self.get_page_text(),
            "page_info": lambda: self.get_page_info()
        }

        if action_type in actions:
            return actions[action_type]()
        return "Unknown action"

    def ask_ollama(self, user_message):
        """Send message to Ollama and get response"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # System prompt to guide the AI
        system_prompt = """You are a browser automation assistant. You can control a web browser.
Available actions:
- navigate: Go to a URL (provide 'url')
- search: Search Amazon (provide 'query')
- click: Click an element (provide 'text')
- screenshot: Take a screenshot (provide 'filename')
- get_text: Get page text
- page_info: Get current page info

Respond with JSON format: {"action": "action_type", "parameters": {...}, "explanation": "why"}
If just chatting, respond normally without JSON."""

        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

        response = ollama.chat(
            model=self.model,
            messages=messages
        )

        ai_response = response['message']['content']
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })

        return ai_response

    def process_ai_response(self, ai_response):
        """Process AI response and execute actions"""
        try:
            # Try to parse as JSON for action
            if "{" in ai_response and "}" in ai_response:
                json_start = ai_response.index("{")
                json_end = ai_response.rindex("}") + 1
                json_str = ai_response[json_start:json_end]
                action_data = json.loads(json_str)

                action = action_data.get("action")
                params = action_data.get("parameters", {})
                explanation = action_data.get("explanation", "")

                print(f"\n🤖 AI Decision: {explanation}")
                print(f"⚡ Executing: {action}")

                result = self.execute_action(action, **params)
                print(f"✅ Result: {result}\n")

                return result
            else:
                # Just a conversational response
                print(f"\n🤖 AI: {ai_response}\n")
                return ai_response

        except json.JSONDecodeError:
            print(f"\n🤖 AI: {ai_response}\n")
            return ai_response
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return str(e)

    def chat(self, message):
        """Main chat interface"""
        print(f"\n👤 You: {message}")
        ai_response = self.ask_ollama(message)
        return self.process_ai_response(ai_response)

    def close_browser(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed!")


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = OllamaAIBrowserAgent(model="llama2")

    # Launch browser
    agent.launch_browser()

    try:
        # Interactive mode
        print("=" * 50)
        print("AI Browser Agent (powered by Ollama)")
        print("=" * 50)

        # Example commands
        agent.chat("Navigate to https://www.amazon.in/ and search 'iphone 14 pro'")
        time.sleep(5)

        agent.chat("Take a screenshot and save it as Amazon.png")
        time.sleep(2)

        agent.chat("Search Amazon for 'iphone 14 pro'")
        time.sleep(3)

        agent.chat("What page am I on right now?")

        # Interactive loop (uncomment to use)
        # while True:
        #     user_input = input("\n👤 You: ")
        #     if user_input.lower() in ['quit', 'exit', 'bye']:
        #         break
        #     agent.chat(user_input)

    finally:
        time.sleep(5)
        agent.close_browser()