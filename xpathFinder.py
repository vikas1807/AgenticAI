import time

import ollama
from selenium import webdriver
from selenium.webdriver.common.by import By


class SimpleXPathGenerator:
    def __init__(self):
        models = ollama.list()
        self.model = 'qwen2.5'
        self.driver = None

    def start(self, url):
        self.driver = webdriver.Chrome()
        self.driver.get(url)
        time.sleep(2)

    def generate_xpath(self, element_description):
        """Generate XPath from description"""
        # Get page title and URL for context
        context = f"Page: {self.driver.title}\nURL: {self.driver.current_url}"

        prompt = f"""{context}

Generate an XPath expression to find: {element_description}

Provide 3 XPath options:
1. Most specific (using ID/unique attributes)
2. By text content
3. By position/class

Format: Just list the 3 XPaths, one per line."""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        xpaths = response['message']['content'].strip().split('\n')
        xpaths = [x.strip() for x in xpaths if x.strip() and '//' in x]

        print(f"\n🤖 Generated XPaths for '{element_description}':")

        for i, xpath in enumerate(xpaths[:3], 1):
            print(f"\n{i}. {xpath}")

            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"   ✅ Found {len(elements)} element(s)")
                else:
                    print(f"   ❌ No elements found")
            except:
                print(f"   ❌ Invalid XPath")

        return xpaths

    def close(self):
        if self.driver:
            self.driver.quit()


# Quick test
if __name__ == "__main__":
    gen = SimpleXPathGenerator()
    gen.start("https://www.amazon.in/")

    gen.generate_xpath("Find Xpath for 'Air conditioners' section")
    #gen.generate_xpath("search button")
    #gen.generate_xpath("navigation menu")
    #gen.generate_xpath("download link")

    time.sleep(3)
    gen.close()