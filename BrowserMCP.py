import ollama

# List all available models on your system
def list_available_models():
    """List all models available in Ollama"""
    try:
        models = ollama.list()
        print("Available models:")
        for model in models['models']:
            print(f"  - {model['name']}")
        return models
    except Exception as e:
        print(f"Error listing models: {e}")
        return None

# Run this to see what you have
list_available_models()