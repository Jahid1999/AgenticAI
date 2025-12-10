from typing import Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel
from app.intro_to_openai_agent import create_agent, run_agent_basic
from app.get_client import ClientName


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class IntroOpenAIResponse(BaseModel):
    message: str
    prompt: str
    client: str
    agent_response: str | None = None
    token_usage: TokenUsage | None = None


app = FastAPI(
    title="Agentic AI API",
    description="API for Agentic AI with OpenAI Agent SDK integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root():
    return {"message": "Welcome to Agentic AI API"}


@app.get("/hello", summary="Say Hello", description="Returns a hello greeting message")
async def say_hello():
    return {"message": "Hello from Agentic AI!"}


@app.get("/health", summary="Health Check", description="Check if the API is running")
async def health_check():
    return {"status": "healthy"}


@app.get(
    "/intro-openai",
    summary="Intro to OpenAI Agent",
    description="Demonstrates OpenAI Agent - pass your prompt and choose a client (openai, deepseek, gemini)",
    response_model=IntroOpenAIResponse,
)
async def intro_openai(
    prompt: str = Query(..., description="The prompt to send to the agent"),
    client: Literal["openai", "deepseek", "gemini"] = Query(
        "openai", description="The AI provider to use"
    ),
):
    try:
        agent = create_agent(client)
        results = await run_agent_basic(agent, prompt, client)

        # Extract token usage from results
        usage = results.raw_responses[-1].usage if results.raw_responses else None
        token_usage = None
        if usage:
            token_usage = TokenUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
            )

        return IntroOpenAIResponse(
            message="Agent executed successfully",
            prompt=prompt,
            client=client,
            agent_response=results.final_output,
            token_usage=token_usage,
        )
    except ValueError as e:
        return IntroOpenAIResponse(message=str(e), prompt=prompt, client=client, agent_response=None)
    except Exception as e:
        return IntroOpenAIResponse(message=f"Error: {str(e)}", prompt=prompt, client=client, agent_response=None)
