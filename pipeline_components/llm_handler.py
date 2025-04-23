import os
from ollama import chat, ResponseError, ListResponse
import ollama

class LLMHandler:
    """Handles interactions with Large Language Models."""

    def __init__(self, logger):
        """Initialize the LLM handler."""
        self.logger = logger

    def check_ollama_running(self):
        """Check if the Ollama service is running."""
        try:
            ollama.ps()
            return True
        except Exception as e:
            self.logger.error(f"Ollama service error: {e}")
            return False

    def list_models(self):
        """List available models in Ollama."""
        try:
            models_list: ListResponse = ollama.list()
            return [m.model for m in models_list["models"]] if "models" in models_list else []
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    def ensure_model_available(self, model_name):
        """Ensure the specified model is available, pull if not."""
        available_models = self.list_models()

        if model_name in available_models:
            return True

        self.logger.debug(f"Model {model_name} not found in the local model list. Pulling from repository.")
        print(f"\nModel '{model_name}' not found locally. Downloading from Ollama registry...\n")
        try:
            ret = os.system(f"ollama pull {model_name}")
            if ret != 0:
                self.logger.critical("Download unsuccessful.")
                return False
            return True
        except Exception as e:
            self.logger.critical(f"Failed to pull the model: {e}")
            return False

    def chat(self, model_name, messages):
        """Send messages to the LLM and get a response."""
        try:
            response = chat(model=model_name, messages=messages)
            return response
        except ResponseError as e:
            self.logger.error(f"LLM response error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during LLM chat: {e}")
            return None
