"""
General Chat Agent
Handles casual conversations and general queries.
"""

from agents import Agent, ModelSettings
from chat_app.config.settings import DEFAULT_MODEL, MAX_OUTPUT_TOKENS


def create_general_agent() -> Agent:
    """Create a general chat agent for casual conversations."""

    instructions = """You are a friendly and helpful general chat assistant.

Your role:
- Engage in casual, friendly conversations
- Answer general knowledge questions
- Provide helpful information on various topics
- Be warm, empathetic, and conversational

Guidelines:
- Keep responses concise and friendly
- Use a conversational tone
- If the question is highly technical or educational, suggest the user might want specialized help
- Be helpful and engaging

Example topics you handle well:
- General questions about daily life
- Weather, news, events
- Recommendations (movies, books, restaurants)
- Casual conversation and small talk
"""

    agent = Agent(
        name="General Chat Assistant",
        instructions=instructions,
        model=DEFAULT_MODEL,
        model_settings=ModelSettings(max_tokens=MAX_OUTPUT_TOKENS),
    )

    return agent
