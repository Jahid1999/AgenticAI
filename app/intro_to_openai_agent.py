"""
Introduction to OpenAI Agents SDK
Demonstrates basic agent creation, execution, and tracing.
"""

import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, set_default_openai_client, trace
from pydantic import BaseModel

from app.get_client import ClientName, get_client, get_model_for_client

# Load environment variables
load_dotenv(override=True)


class SimpleRunResult(BaseModel):
    """Simple result structure for non-OpenAI providers"""
    final_output: str
    raw_responses: list

    class Config:
        arbitrary_types_allowed = True


def create_agent(client_name: ClientName = "openai"):
    """Create a history agent with the specified client."""
    model = get_model_for_client(client_name)
    agent = Agent(
        name="History Agent",
        instructions="You have enough knowledge about history. You are able to answer questions related to historical events, dates, and figures.",
        model=model,
    )
    return agent


async def run_agent_basic(agent: Agent, prompt: str, client_name: ClientName = "openai"):
    """Run the agent with a prompt and display results."""
    # Get and set the client for this provider
    client = get_client(client_name)

    # For OpenAI, use the Agents SDK which requires the /responses endpoint
    if client_name == "openai":
        set_default_openai_client(client)
        results = await Runner.run(agent, prompt)
        print("Full Results:")
        print(results)
        print("\nFinal Output:")
        print(results.final_output)
        return results

    # For DeepSeek and Gemini, use direct chat completions API
    # They don't support the /responses endpoint used by Agents SDK
    else:
        model = get_model_for_client(client_name)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": agent.instructions},
                {"role": "user", "content": prompt}
            ]
        )

        final_output = response.choices[0].message.content
        print("Full Results:")
        print(f"Response from {client_name}")
        print("\nFinal Output:")
        print(final_output)

        # Create a compatible result object
        results = SimpleRunResult(
            final_output=final_output,
            raw_responses=[response]
        )
        return results


async def run_agent_with_trace(agent: Agent, prompt: str, client_name: ClientName = "openai"):
    """Run the agent with tracing enabled (OpenAI only)."""
    if client_name != "openai":
        print(f"Warning: Tracing only supported for OpenAI. Falling back to basic run for {client_name}")
        return await run_agent_basic(agent, prompt, client_name)

    client = get_client(client_name)
    set_default_openai_client(client)

    with trace("Answering question"):
        results = await Runner.run(agent, prompt)
        print(results.final_output)
    return results


async def main():
    """Main entry point demonstrating OpenAI Agents SDK usage."""
    # Choose which client to use: "openai", "deepseek", or "gemini"
    client_name: ClientName = "openai"

    # Create the agent with the specified client
    agent = create_agent(client_name)
    print(f"\nAgent created: {agent}")

    # Run the agent with a basic prompt
    print("\n--- Basic Agent Run ---")
    await run_agent_basic(agent, "Tell me about World War 2.", client_name)

    # Run with tracing
    print("\n--- Traced Agent Run ---")
    await run_agent_with_trace(agent, "Who won the 2022 FIFA World Cup?", client_name)


if __name__ == "__main__":
    asyncio.run(main())
