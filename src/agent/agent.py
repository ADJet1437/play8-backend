import os
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.ai_completion import AICompletion
from src.agent.tools import generate_training_cards

SPORTS_SYSTEM_PROMPT = """You are a helpful AI assistant specialized in sports, particularly tennis and athletic training.
You provide expert advice on:
- Tennis techniques and strategies
- Training routines and exercises
- Sports equipment and gear
- Injury prevention and recovery
- Performance improvement tips
- General sports knowledge

Keep your responses concise, practical, and focused on sports-related topics. If asked about non-sports topics, politely redirect to sports-related advice."""

TOOL_DECISION_PROMPT = """Based on the conversation, decide whether to generate training/technique cards.
Only generate cards if the conversation involves sports training, techniques, drills, or exercises.
If the conversation is casual or unrelated to actionable training content, do NOT call any tools."""


class Agent:
    def __init__(self):
        # Text-only LLM (no tools bound)
        self.text_completion = AICompletion(
            temperature=0.7,
            max_tokens=2000,
        )
        # Tool-calling LLM (tools bound, not streamed to user)
        self.tool_completion = AICompletion(
            temperature=0.7,
            max_tokens=2000,
        )
        self.tools = [generate_training_cards]
        self.tool_map = {t.name: t for t in self.tools}
        self.tool_completion.bind_tools(self.tools)

    def _build_messages(self, message: str, conversation_history: list[dict]) -> list:
        messages = [SystemMessage(content=SPORTS_SYSTEM_PROMPT)]
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=message))
        return messages

    async def run(
        self, message: str, conversation_history: list[dict]
    ) -> AsyncGenerator[dict, None]:
        messages = self._build_messages(message, conversation_history)

        # Phase 1: Stream text response (no tools)
        text_content = ""
        async for chunk in self.text_completion.get_stream_response(messages):
            if chunk.content:
                text_content += chunk.content
                yield {"type": "text_delta", "content": chunk.content}

        # Phase 2: Decide whether to generate cards (non-streamed tool call)
        tool_messages = [
            SystemMessage(content=TOOL_DECISION_PROMPT),
            *messages[1:],  # skip original system prompt, keep history + user message
            AIMessage(content=text_content),  # include the text response as context
        ]

        full_response = None
        async for chunk in self.tool_completion.get_stream_response(tool_messages):
            full_response = chunk if full_response is None else full_response + chunk

        if full_response and full_response.tool_calls:
            for tool_call in full_response.tool_calls:
                tool_fn = self.tool_map.get(tool_call["name"])
                if tool_fn:
                    result = tool_fn.invoke(tool_call["args"])
                    yield {
                        "type": "tool_use_end",
                        "id": tool_call["id"],
                        "tool": tool_call["name"],
                        "result": result,
                    }

    async def generate_title(self, message: str) -> str:
        """Generate a short conversation title from the first user message."""
        try:
            title_llm = AICompletion(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.5,
                max_tokens=20,
            )
            messages = [
                SystemMessage(
                    content="Generate a short title (max 6 words) for a conversation. Reply with ONLY the title, no quotes or punctuation."
                ),
                HumanMessage(content=message),
            ]
            full = None
            async for chunk in title_llm.get_stream_response(messages):
                full = chunk if full is None else full + chunk
            return full.content.strip() if full and full.content else message[:50]
        except Exception:
            return message[:50] + ("..." if len(message) > 50 else "")
