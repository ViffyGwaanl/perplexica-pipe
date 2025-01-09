"""
title: perplexica pipe
author: open-webui, gwaanl
author_url：https://github.com/ViffyGwaanl/perplexica-pipe
You can find the instructions and submit questions at the website above
funding_url: https://github.com/ViffyGwaanl
version: 0.3.4
required_open_webui_version: 0.5.3

0.1.1：Create code to implement the "pipeline" function using the Perplexica search API
0.2.1：Increased contextual memory function, which can record historical conversation data 
and send the history to the Perplexica API for more accurate searches each time a search is performed.
0.2.2：Change the model display name to the following format "Perplexica/gpt-4o/academicSearch"
0.3.1：Added the option to select a local model, which can be configured to use OpenAI or Ollama in perplexica_provider
0.3.2：Configure the provider for embeddingModel and chatModel separately
0.3.3: Added customOpenAIKey and customOpenAIBaseURL for custom OpenAI instances
0.3.4: Fixed the issue that caused openwebui to fail to start when the values of customOpenAIBaseURL and customOpenAIKey were none
"""

from typing import List, Union
from pydantic import BaseModel, Field
import requests


class Pipe:
    class Valves(BaseModel):
        # Perplexica API configuration
        enable_perplexica: bool = Field(
            default=True
        )  # Enable Perplexica search (default: True)
        perplexica_api_url: str = Field(
            default="http://localhost:3001/api/search"
        )  # Perplexica API URL
        perplexica_chat_provider: str = Field(
            default="openai"
        )  # Provider for chat model
        perplexica_chat_model: str = Field(
            default="gpt-4o-mini"
        )  # Chat model to use (default: gpt-4o-mini)
        perplexica_embedding_provider: str = Field(
            default="openai"
        )  # Provider for embedding model
        perplexica_embedding_model: str = Field(
            default="text-embedding-3-large"
        )  # Embedding model to use (default: text-embedding-3-large)
        perplexica_focus_mode: str = Field(
            default="webSearch"
        )  # Focus mode for search (default: webSearch)
        perplexica_optimization_mode: str = Field(
            default="balanced"
        )  # Optimization mode for search (default: balanced)
        # Custom OpenAI configuration
        customOpenAIBaseURL: str = Field(
            default="https://api.xxxx.com/v1"
        )  # Base URL for custom OpenAI instance
        customOpenAIKey: str = Field(
            default="sk-xxxxxxx"
        )  # API key for custom OpenAI instance

    def __init__(self):
        self.type = "manifold"  # Pipe type
        self.id = "perplexica_pipe"  # Pipe ID
        self.name = "Perplexica/"  # Pipe name
        self.valves = self.Valves()  # Initialize Valves instance
        self.history = []  # Initialize history list for storing conversation history

    def pipes(self) -> List[dict]:
        """Return a list of enabled pipes."""
        enabled_pipes = []
        if self.valves.enable_perplexica:
            enabled_pipes.append(
                {
                    "id": "perplexica",
                    "name": f"{self.valves.perplexica_chat_model}/{self.valves.perplexica_focus_mode}",
                }
            )
        return enabled_pipes

    def pipe(self, body: dict, results=None) -> Union[str, dict]:
        """Process the request and return the search results."""
        user_input = self._extract_user_input(
            body
        )  # Extract user input from the request body
        if not user_input:
            return "No search query provided"  # Return an error message if no user input is provided

        model = body.get("model", "")  # Get the model name from the request body
        print(f"Received model: {model}")  # Print the received model name

        if "perplexica" in model.lower() and self.valves.enable_perplexica:
            print("Calling Perplexica search")
            response = self._search_perplexica(
                user_input, results
            )  # Get search results
            self._update_history(user_input, response)  # Update conversation history
            return response  # Return the search results
        else:
            return f"Unsupported or disabled search engine for model: {model}"  # Return an error message if the search engine is not supported or disabled

    def _update_history(self, user_input: str, response: str):
        """Update the conversation history."""
        self.history.append(["human", user_input])  # Add user input to history
        self.history.append(["assistant", response])  # Add search results to history

    def _extract_user_input(self, body: dict) -> str:
        """Extract user input from the request body."""
        messages = body.get(
            "messages", []
        )  # Get the messages list from the request body
        if messages:
            last_message = messages[-1]  # Get the last message in the list
            if isinstance(
                last_message.get("content"), list
            ):  # Check if the content of the last message is a list
                for item in last_message["content"]:  # Iterate through the list
                    if item["type"] == "text":  # Check if the item type is "text"
                        return item["text"]  # Return the text content of the item
            else:
                return last_message.get(
                    "content", ""
                )  # Return the content of the last message if it is not a list
        return ""  # Return an empty string if no user input is found

    def _search_perplexica(self, query: str, results=None) -> str:
        """Execute a search using the Perplexica Search API."""
        if not self.valves.enable_perplexica:
            return "Perplexica search is disabled"  # Return an error message if Perplexica search is disabled

        print("Searching with Perplexica")
        try:
            # Build request body
            request_body = {
                "chatModel": {
                    "provider": self.valves.perplexica_chat_provider,
                    "model": self.valves.perplexica_chat_model,
                    # Add custom OpenAI configuration if provided
                    "customOpenAIBaseURL": self.valves.customOpenAIBaseURL,
                    "customOpenAIKey": self.valves.customOpenAIKey,
                },
                "embeddingModel": {
                    "provider": self.valves.perplexica_embedding_provider,
                    "model": self.valves.perplexica_embedding_model,
                },
                "optimizationMode": self.valves.perplexica_optimization_mode,  # Use the configured optimization mode
                "focusMode": self.valves.perplexica_focus_mode,
                "query": query,  # User search query
                "history": self.history,  # Add history parameter
            }

            # Remove None values from request_body
            request_body = {k: v for k, v in request_body.items() if v is not None}

            headers = {"Content-Type": "application/json"}  # Set request headers

            response = requests.post(
                self.valves.perplexica_api_url,
                json=request_body,
                headers=headers,  # Send POST request to Perplexica API
            )
            response.raise_for_status()  # Raise an exception if the request failed

            search_results = response.json()  # Parse the response JSON data

            # Formatted result
            formatted_results = (
                f"Perplexica Search Results:\n\n"  # Initialize formatted results string
            )
            formatted_results += (
                search_results.get("message", "No message available")
                + "\n\n"  # Add the message from the search results
            )
            for i, source in enumerate(
                search_results.get("sources", []), 1
            ):  # Iterate through the sources in the search results
                title = source["metadata"].get(
                    "title", "No title"
                )  # Get the title of the source
                snippet = source.get(
                    "pageContent", "No snippet available"
                )  # Get the snippet of the source
                link = source["metadata"].get(
                    "url", "No URL available"
                )  # Get the URL of the source
                formatted_results += f"{i}. {title}\n URL: {link}\n\n"  # Add the formatted source information to the results string

            return formatted_results  # Return the formatted results string

        except Exception as e:
            return f"An error occurred while searching Perplexica: {str(e)}"  # Return an error message if an exception occurred during the search
