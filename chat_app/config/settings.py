"""
Configuration settings for the chat application.
"""

from typing import Literal

# AI Model Configuration
DEFAULT_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7
TOP_P = 0.9

# Agent Types
AgentType = Literal["triage", "general", "technical", "student"]

# Triage keywords for routing
TECHNICAL_KEYWORDS = [
    "code", "programming", "debug", "error", "api", "database",
    "algorithm", "function", "class", "bug", "implementation",
    "software", "develop", "technical", "python", "javascript",
    "java", "c++", "sql", "framework", "library"
]

STUDENT_KEYWORDS = [
    "homework", "assignment", "study", "learn", "explain",
    "tutorial", "lesson", "course", "exam", "test",
    "understand", "concept", "basics", "beginner", "teach"
]

# UI Configuration
APP_TITLE = "Multi-Agent Chat Assistant"
APP_DESCRIPTION = """
Welcome to the Multi-Agent Chat Assistant!

This system automatically routes your questions to specialized agents:
- 🤖 **General Chat**: Casual conversations and general queries
- 💻 **Technical Expert**: Programming, debugging, and technical questions
- 📚 **Student Helper**: Educational content, homework help, and learning

Just ask your question naturally, and the system will route it to the best agent!
"""

# API Configuration
HOST = "0.0.0.0"
PORT = 8000
