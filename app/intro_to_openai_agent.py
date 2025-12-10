"""
Introduction to OpenAI Agents SDK
Demonstrates basic agent creation, execution, and tracing.
"""

import os
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace

# Load environment variables
load_dotenv(override=True)


def check_api_key():
    """Verify OpenAI API key is set."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
    else:
        print(f"OpenAI API exists: {openai_api_key[:10]}...")
    return openai_api_key


def create_agent():
    """Create a history agent."""
    agent = Agent(
        name="History Agent",
        instructions="You have enough knowledge about history. You are able to answer questions related to historical events, dates, and figures.",
        model="gpt-5-mini",
    )
    return agent


async def run_agent_basic(agent: Agent, prompt: str):
    """Run the agent with a prompt and display results."""
    results = await Runner.run(agent, prompt)
    print("Full Results:")
    print(results)
    print("\nFinal Output:")
    print(results.final_output)
    return results


async def run_agent_with_trace(agent: Agent, prompt: str):
    """Run the agent with tracing enabled."""
    with trace("Answering question"):
        results = await Runner.run(agent, prompt)
        print(results.final_output)
    return results


async def main():
    """Main entry point demonstrating OpenAI Agents SDK usage."""
    # Step 1: Check API key
    check_api_key()

    # Step 2: Create the agent
    agent = create_agent()
    print(f"\nAgent created: {agent}")

    # Step 3: Run the agent with a basic prompt
    print("\n--- Basic Agent Run ---")
    await run_agent_basic(agent, "Tell me a joke about autonomous agents.")

    # Step 4: Run with tracing
    print("\n--- Traced Agent Run ---")
    await run_agent_with_trace(agent, "Tell me a joke about autonomous agents.")


if __name__ == "__main__":
    asyncio.run(main())
