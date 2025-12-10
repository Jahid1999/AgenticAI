# Agentic AI - Multi-Agent Chat System

FastAPI backend with multi-agent chat system featuring intelligent routing.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start
docker-compose up -d

# Stop
docker-compose down
```

### Using Docker

```bash
# Build
docker build -t agentic-ai .

# Run
docker run -p 8000:8000 --env-file .env agentic-ai
```

## Access

- **API Docs:** http://localhost:8000/docs
- **Chat API:** http://localhost:8000/api/chat/message
- **Root:** http://localhost:8000

## Environment

Create `.env` file:
```env
OPENAI_API_KEY=sk-your-key-here
```

## Features

- Multi-agent chat with intelligent routing
- FastAPI REST API
- Agent specializations: General, Technical, Student
- Automatic agent handoffs based on query type
