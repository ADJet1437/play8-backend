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
        max_tokens: int = 2000,
    ):
        self.llm = ChatOpenAI(
            model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )

    def bind_tools(self, tools: list) -> None:
        self.llm = self.llm.bind_tools(tools)

    async def get_stream_response(
        self, messages: list[BaseMessage]
    ) -> AsyncGenerator[AIMessageChunk, None]:
        async for chunk in self.llm.astream(messages):
            yield chunk
