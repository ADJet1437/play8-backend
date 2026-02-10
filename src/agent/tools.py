import json

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class TrainingCardContent(BaseModel):
    overview: str = Field(description="2-3 sentences explaining the card")
    steps: list[str] = Field(description="4 actionable steps")
    tips: list[str] = Field(description="3 practical tips")
    duration: str = Field(description="e.g. 2 weeks, 30 min, 1 day")
    difficulty: str = Field(description="beginner, intermediate, or advanced")


class TrainingCard(BaseModel):
    title: str = Field(description="Short card title (3-5 words)")
    description: str = Field(description="One sentence description")
    category: str = Field(description="training, technique, or ball-machine")
    content: TrainingCardContent


@tool
def generate_training_cards(cards: list[TrainingCard]) -> str:
    """Use this when the user asks about training, techniques, drills, or exercises.
    Generate 1-2 training/technique cards with actionable content.
    Each card should be specific to what the user is discussing."""
    return json.dumps([card.model_dump() for card in cards])
