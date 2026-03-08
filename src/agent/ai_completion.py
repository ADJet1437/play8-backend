import os
from collections.abc import AsyncGenerator

from langchain_core.messages import BaseMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_openai import ChatOpenAI


class AICompletion:
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ):
        llm_params = {
            "model": model or "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": temperature,
            "streaming": True,
        }
        if max_tokens is not None:
            llm_params["max_tokens"] = max_tokens

        self.llm = ChatOpenAI(**llm_params)

    def bind_tools(self, tools: list) -> None:
        self.llm = self.llm.bind_tools(tools)

    async def get_stream_response(
        self, messages: list[BaseMessage]
    ) -> AsyncGenerator[AIMessageChunk, None]:
        async for chunk in self.llm.astream(messages):
            yield chunk
