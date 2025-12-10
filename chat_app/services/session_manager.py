"""
Session Manager for Conversation Memory
Manages conversation history per session with automatic cleanup.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from chat_app.config.settings import SESSION_TIMEOUT_MINUTES, MAX_HISTORY_MESSAGES


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_used: Optional[str] = None


@dataclass
class Session:
    """Represents a user session with conversation history."""
    session_id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str, agent_used: Optional[str] = None) -> None:
        """Add a message to the session history."""
        self.messages.append(Message(role=role, content=content, agent_used=agent_used))
        self.last_activity = datetime.now()

        # Keep only the last N messages
        if len(self.messages) > MAX_HISTORY_MESSAGES:
            self.messages = self.messages[-MAX_HISTORY_MESSAGES:]

    def get_history_for_agent(self) -> list[dict]:
        """Get conversation history in format suitable for the agent."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def is_expired(self) -> bool:
        """Check if session has expired due to inactivity."""
        timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        return datetime.now() - self.last_activity > timeout


class SessionManager:
    """Manages multiple user sessions with automatic cleanup."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(session_id=session_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID, returns None if not found or expired."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired():
            self.delete_session(session_id)
            return None
        return session

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create a new one."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        # Create new session
        new_id = self.create_session()
        return self._sessions[new_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_used: Optional[str] = None
    ) -> None:
        """Add a message to a session."""
        session = self.get_session(session_id)
        if session:
            session.add_message(role, content, agent_used)

    def get_history(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        session = self.get_session(session_id)
        if session:
            return session.get_history_for_agent()
        return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and return True if it existed."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions and return count of removed."""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()
