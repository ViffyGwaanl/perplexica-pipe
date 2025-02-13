"""
title: perplexica pipe
author: open-webui, gwaanl
author_url: https://github.com/ViffyGwaanl/perplexica-pipe
You can find the instructions and submit questions at the website above
funding_url: https://github.com/ViffyGwaanl
version: 0.3.7
required_open_webui_version: 0.5.3

0.1.1：Create code to implement the "pipeline" function using the Perplexica search API
0.2.1：Increased contextual memory function, which can record historical conversation data 
and send the history to the Perplexica API for more accurate searches each time a search is performed.
0.2.2：Change the model display name to the following format "Perplexica/gpt-4o/academicSearch"
0.3.1：Added the option to select a local model, which can be configured to use OpenAI or Ollama in perplexica_provider
0.3.2：Configure the provider for embeddingModel and chatModel separately
0.3.3: Added customOpenAIKey and customOpenAIBaseURL for custom OpenAI instances
0.3.4: Fixed the issue that caused openwebui to fail to start when the values of customOpenAIBaseURL and customOpenAIKey were none,
If you installed 0.3.3 and it caused openwebui to fail to start, please find the solution at author_url.
0.3.5: Optimized the default values and the cleared content of the request body
0.3.6: added Task bypass, refactored pipe to be async, added event emmiters, added propper emitter for the final results
0.3.7: refactored to use aiohttp, added better sources formating
0.3.8: removed response header.
"""

from typing import List, Union, Dict
from pydantic import BaseModel, Field
from dataclasses import dataclass
from open_webui.constants import TASKS
from open_webui.utils.chat import generate_chat_completion
import aiohttp


@dataclass
class User:
    id: str
    email: str
    name: str
    role: str


name = "Perplexica/"



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
            default="default"
        )  # Base URL for custom OpenAI instance
        customOpenAIKey: str = Field(
            default="default"
        )  # API key for custom OpenAI instance
        task_model: str = Field(default="gpt-4o-mini")  # model tag for task bypass

    def __init__(self):
        self.type = "manifold"  # Pipe type
        self.id = "perplexica_pipe"  # Pipe ID
        self.name = name  # Pipe name
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

    async def emit_status(self, level: str, message: str, done: bool):
        await self.__current_event_emitter__(
            {
                "type": "status",
                "data": {
                    "status": "complete" if done else "in_progress",
                    "level": level,
                    "description": message,
                    "done": done,
                },
            }
        )

    async def emit_message(self, message: str):
        await self.__current_event_emitter__(
            {"type": "message", "data": {"content": message}}
        )

    async def pipe(
        self,
        body: dict,
        __user__: dict,
        __event_emitter__=None,
        __task__=None,
        __model__=None,
        __request__=None,
        results=None,
    ) -> Union[str, dict]:
        """Process the request and return the search results."""
        user_input = self._extract_user_input(body)
        model = self.valves.task_model
        self.__user__ = User(**__user__)
        self.__request__ = __request__
        self.__current_event_emitter__ = __event_emitter__
        if __task__ and __task__ != TASKS.DEFAULT:
            response = await generate_chat_completion(
                self.__request__,
                {"model": model, "messages": body.get("messages"), "stream": False},
                user=self.__user__,
            )
            return f"{name}: {response['choices'][0]['message']['content']}"
        if not user_input:
            return "No search query provided"  # Return an error message if no user input is provided

        model = body.get("model", "")
        print(f"Received model: {model}")

        if "perplexica" in model.lower() and self.valves.enable_perplexica:
            await self.emit_status("info", "Searching...", False)
            print("Calling Perplexica search")
            response = await self._search_perplexica(user_input, results)
            self._update_history(user_input, response)
            await self.emit_message(response)
            print(response)
            await self.emit_status("info", "Search Completed", True)
            return response  # Return the search results
        else:
            return f"Unsupported or disabled search engine for model: {model}"

    def _update_history(self, user_input: str, response: str):
        """Update the conversation history."""
        self.history.append(["human", user_input])
        self.history.append(["assistant", response])

    def _extract_user_input(self, body: dict) -> str:
        """Extract user input from the request body."""
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

    async def _search_perplexica(self, query: str, results=None) -> str:
        """Execute a search using the Perplexica Search API."""
        if not self.valves.enable_perplexica:
            return "Perplexica search is disabled"

        print("Searching with Perplexica")
        try:
            # Build request body
            request_body = {
                "chatModel": {
                    "provider": self.valves.perplexica_chat_provider,
                    "model": self.valves.perplexica_chat_model,
                    "customOpenAIBaseURL": self.valves.customOpenAIBaseURL,
                    "customOpenAIKey": self.valves.customOpenAIKey,
                },
                "embeddingModel": {
                    "provider": self.valves.perplexica_embedding_provider,
                    "model": self.valves.perplexica_embedding_model,
                },
                "optimizationMode": self.valves.perplexica_optimization_mode,
                "focusMode": self.valves.perplexica_focus_mode,
                "query": query,
                "history": self.history,
            }

            # Remove None values and "default" strings from request_body
            request_body = {k: v for k, v in request_body.items() if v is not None}
            request_body = {k: v for k, v in request_body.items() if v != "default"}
            headers = {"Content-Type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.valves.perplexica_api_url, json=request_body, headers=headers
                ) as response:
                    response.raise_for_status()
                    search_results = await response.json()

            # Use the number of sources (n_sources) instead of a timer
            n_sources = len(search_results.get("sources", []))

            # Build the details block that now includes the sources inside it
            header = f"Web search found {n_sources} sources"
            details_block = (
                f'<details type="web search" done="true" count="{n_sources}">\n'
                f"<summary>{header}</summary>\n"
                f"> {n_sources} sources found\n\n"
            )
            for i, source in enumerate(search_results.get("sources", []), 1):
                title = source["metadata"].get("title", "No title")
                snippet = source.get("pageContent", "No snippet available")
                link = source["metadata"].get("url", "No URL available")
                details_block += f"{i}. {title}\n URL: {link}\n\n"
            details_block += "</details>\n\n"

            # Retrieve and clean the message
            message_content = search_results.get("message", "No message available")
            # If message starts exactly with "Perplexica Search Results:", remove it
            prefix = "Perplexica Search Results:"
            if message_content.startswith(prefix):
                message_content = message_content[len(prefix) :].lstrip()

            # Build the final formatted result string
            formatted_results = details_block
            formatted_results += message_content + "\n\n"

            return formatted_results

        except Exception as e:
            await self.emit_status("info", f"Error: {str(e)}", True)
            return "An error occurred during the Perplexica search."
