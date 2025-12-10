from typing import Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel
from app.intro_to_openai_agent import create_agent, run_agent_basic
from app.get_client import ClientName
from app.guardrails_and_handoffs import process_with_guardrails_and_handoffs, HandoffResult


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
        # Handle both OpenAI Agents SDK results and direct API results
        token_usage = None
        if results.raw_responses:
            response = results.raw_responses[-1]
            # Check if it's an OpenAI Agents SDK response or direct API response
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                # Handle both Agent SDK format and standard OpenAI format
                token_usage = TokenUsage(
                    input_tokens=getattr(usage, 'input_tokens', getattr(usage, 'prompt_tokens', 0)),
                    output_tokens=getattr(usage, 'output_tokens', getattr(usage, 'completion_tokens', 0)),
                    total_tokens=getattr(usage, 'total_tokens', 0),
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


@app.post(
    "/guardrails-handoffs",
    summary="Guardrails and Agent Handoffs",
    description="Demonstrates input/output guardrails and automatic agent routing with handoffs",
    response_model=HandoffResult,
)
async def guardrails_handoffs(
    user_input: str = Query(..., description="The user input to process"),
    client: Literal["openai", "deepseek", "gemini"] = Query(
        "openai", description="The AI provider to use"
    ),
):
    """
    Process user input with complete guardrails and agent handoffs.
    """
    try:
        result = await process_with_guardrails_and_handoffs(user_input, client)
        return result
    except Exception as e:
        import traceback
        print(f"Exception: {str(e)}")
        print(traceback.format_exc())
        return HandoffResult(
            success=False,
            routed_to="error",
            final_response="",
            input_guardrail_passed=False,
            output_guardrail_passed=False,
            errors=[f"Error: {str(e)}"]
        )
