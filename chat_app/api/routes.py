"""
API Routes for Chat Application
Handles chat requests and agent orchestration.
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from agents import Runner, set_default_openai_client

from chat_app.agents.general_agent import create_general_agent
from chat_app.agents.technical_agent import create_technical_agent
from chat_app.agents.student_agent import create_student_agent
from chat_app.agents.triage_agent import create_triage_agent
from app.get_client import get_client


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    conversation_history: Optional[list] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    agent_used: str
    success: bool
    error: Optional[str] = None


# Create router
router = APIRouter(prefix="/api/chat", tags=["Chat API"])


# Initialize agents (singleton pattern)
_agents_initialized = False
_triage_agent = None


def initialize_agents():
    """Initialize all agents (called once)."""
    global _agents_initialized, _triage_agent

    if not _agents_initialized:
        # Setup OpenAI client
        client = get_client("openai")
        set_default_openai_client(client)

        # Create specialized agents
        general_agent = create_general_agent()
        technical_agent = create_technical_agent()
        student_agent = create_student_agent()

        # Create triage agent with handoffs
        _triage_agent = create_triage_agent(
            general_agent=general_agent,
            technical_agent=technical_agent,
            student_agent=student_agent
        )

        _agents_initialized = True


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the chat system.

    The triage agent will automatically route to the appropriate specialist.

    Args:
        request: ChatRequest with user message

    Returns:
        ChatResponse with agent reply
    """
    try:
        # Initialize agents if needed
        initialize_agents()

        # Run the triage agent (it will handle routing)
        result = await Runner.run(_triage_agent, request.message)

        # Extract response
        response_text = result.final_output
        agent_name = result.agent.name if hasattr(result, 'agent') else "Triage Assistant"

        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            success=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "multi-agent-chat"}


@router.post("/reset")
async def reset_conversation():
    """Reset conversation history."""
    # In a production system, you'd clear session-specific history
    return {"status": "conversation_reset", "message": "Conversation history cleared"}
