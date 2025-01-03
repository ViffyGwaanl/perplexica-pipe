"""
title: perplexica pipe
author: open-webui, gwaanl
author_url: https://github.com/ViffyGwaanl
funding_url: https://github.com/open-webui
version: 0.1.1
required_open_webui_version: 0.5.3

"""


from typing import List, Union
from pydantic import BaseModel, Field
import requests


class Pipe:
    class Valves(BaseModel):
        # Perplexica API configuration
        enable_perplexica: bool = Field(default=True)
        perplexica_api_url: str = Field(default="http://localhost:3001/api/search")
        perplexica_chat_model: str = Field(default="gpt-4o-mini")
        perplexica_embedding_model: str = Field(default="text-embedding-3-large")
        perplexica_focus_mode: str = Field(default="webSearch")
        perplexica_optimization_mode: str = Field(
            default="balanced"
        )  # Add optimization mode configuration

    def __init__(self):
        self.type = "manifold"
        self.id = "engine_search"
        self.name = "Perplexica/"
        self.valves = self.Valves()

    def pipes(self) -> List[dict]:
        enabled_pipes = []
        if self.valves.enable_perplexica:
            enabled_pipes.append(
                {"id": "perplexica", "name": self.valves.perplexica_focus_mode}
            )
        return enabled_pipes

    def pipe(self, body: dict, results=None) -> Union[str, dict]:
        user_input = self._extract_user_input(body)
        if not user_input:
            return "No search query provided"

        model = body.get("model", "")
        print(f"Received model: {model}")


        if "perplexica" in model.lower() and self.valves.enable_perplexica:
            print("Calling Perplexica search")
            return self._search_perplexica(user_input, results)
        else:
            return f"Unsupported or disabled search engine for model: {model}"

    def _extract_user_input(self, body: dict) -> str:
        messages = body.get("messages", [])
        if messages:
            last_message = messages[-1]
            if isinstance(last_message.get("content"), list):
                for item in last_message["content"]:
                    if item["type"] == "text":
                        return item["text"]
            else:
                return last_message.get("content", "")
        return ""

    def _search_perplexica(self, query: str, results=None) -> str:
        """Execute a search using the Perplexica Search API"""
        if not self.valves.enable_perplexica:
            return "Perplexica search is disabled"

        print("Searching with Perplexica")
        try:
            # Build request body
            request_body = {
                "chatModel": {
                    "provider": "openai",
                    "model": self.valves.perplexica_chat_model,
                },
                "embeddingModel": {
                    "provider": "openai",
                    "model": self.valves.perplexica_embedding_model,
                },
                "optimizationMode": self.valves.perplexica_optimization_mode,  # Use the configured optimization mode
                "focusMode": self.valves.perplexica_focus_mode,
                "query": query,
“历史”： []，
            }

            headers = {"Content-Type": "application/json"}

            response = requests.post(
                self.valves.perplexica_api_url, json=request_body, headers=headers
            )
            response.raise_for_status()

            search_results = response.json()

            # Formatted result
            formatted_results = f"Perplexica Search Results:\n\n"
            formatted_results += (
                search_results.get("message", "No message available") + "\n\n"
            )
            for i, source in enumerate(search_results.get("sources", []), 1):
                title = source["metadata"].get("title", "No title")
                snippet = source.get("pageContent", "No snippet available")
                link = source["metadata"].get("url", "No URL available")
                formatted_results += f"{i}. {title}\n URL: {link}\n\n"

            return formatted_results

        except Exception as e:
            return f"An error occurred while searching Perplexica: {str(e)}"
