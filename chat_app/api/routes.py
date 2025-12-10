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
from chat_app.services.session_manager import session_manager
from app.get_client import get_client


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    agent_used: str
    success: bool
    session_id: str
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
    Maintains conversation history per session.

    Args:
        request: ChatRequest with user message and optional session_id

    Returns:
        ChatResponse with agent reply and session_id
    """
    try:
        # Initialize agents if needed
        initialize_agents()

        # Get or create session for conversation memory
        session = session_manager.get_or_create_session(request.session_id)

        # Add user message to history
        session.add_message("user", request.message)

        # Get conversation history for context
        history = session.get_history_for_agent()

        # Run the triage agent with conversation history
        result = await Runner.run(_triage_agent, history)

        # Extract response
        response_text = result.final_output
        agent_name = result.last_agent.name if hasattr(result, 'last_agent') else "Triage Assistant"

        # Add assistant response to history
        session.add_message("assistant", response_text, agent_used=agent_name)

        return ChatResponse(
            response=response_text,
            agent_used=agent_name,
            success=True,
            session_id=session.session_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "multi-agent-chat",
        "active_sessions": session_manager.get_session_count()
    }


@router.post("/reset")
async def reset_conversation(session_id: Optional[str] = None):
    """Reset conversation history for a session."""
    if session_id:
        deleted = session_manager.delete_session(session_id)
        if deleted:
            return {"status": "conversation_reset", "message": "Session cleared successfully"}
        return {"status": "not_found", "message": "Session not found"}

    return {"status": "error", "message": "No session_id provided"}


@router.post("/session/new")
async def create_new_session():
    """Create a new chat session."""
    session_id = session_manager.create_session()
    return {"session_id": session_id, "message": "New session created"}


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "agent_used": msg.agent_used,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
    }
