"""
Guardrails and Handoffs with OpenAI Agents SDK
Demonstrates simple input/output guardrails and agent handoffs.
"""

import asyncio
import re
from typing import Optional
from dotenv import load_dotenv
from agents import Agent, Runner, set_default_openai_client, InputGuardrail, OutputGuardrail, GuardrailFunctionOutput
from pydantic import BaseModel

from app.get_client import ClientName, get_client, get_model_for_client

# Load environment variables
load_dotenv(override=True)


# ============================================================================
# INPUT GUARDRAIL - Single simple function
# ============================================================================

async def check_unsafe_content(ctx, agent, input_data: str):
    """
    Check if input contains unsafe or inappropriate content.

    Args:
        ctx: The context object (passed by SDK)
        agent: The agent instance (passed by SDK)
        input_data: The actual content to check

    Returns:
        GuardrailFunctionOutput with tripwire_triggered flag
    """
    # Check for prohibited patterns
    unsafe_patterns = [
        r'\b(hack|exploit|attack|malware|virus)\b',
        r'\b(steal|leak|bypass)\b.*\b(data|password|system)\b',
        r'\b(illegal|harmful)\b.*\b(activity|content)\b',
    ]

    content_lower = input_data.lower()

    # Check if empty
    if len(input_data.strip()) == 0:
        return GuardrailFunctionOutput(
            output_info={"is_safe": False, "reason": "Input cannot be empty."},
            tripwire_triggered=True,
        )

    # Check for unsafe patterns
    for pattern in unsafe_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return GuardrailFunctionOutput(
                output_info={"is_safe": False, "reason": "Input contains unsafe content and cannot be processed."},
                tripwire_triggered=True,
            )

    # Input is safe
    return GuardrailFunctionOutput(
        output_info={"is_safe": True, "reason": "Input passed safety checks."},
        tripwire_triggered=False,
    )


# ============================================================================
# OUTPUT GUARDRAIL - Single simple function
# ============================================================================

async def check_unsafe_output(ctx, agent, output_data: str):
    """
    Check if output contains harmful or inappropriate content.

    Args:
        ctx: The context object (passed by SDK)
        agent: The agent instance (passed by SDK)
        output_data: The actual content to check

    Returns:
        GuardrailFunctionOutput with tripwire_triggered flag
    """
    # Check for harmful content in output
    harmful_patterns = [
        r'\b(how to|guide|instructions).*(harm|hurt|attack)\b',
        r'\b(illegal|unlawful).*(activity|method)\b',
    ]

    content_lower = output_data.lower()

    # Check if output is too short
    if len(output_data.strip()) < 10:
        return GuardrailFunctionOutput(
            output_info={"is_safe": False, "reason": "Output is too short or empty."},
            tripwire_triggered=True,
        )

    # Check for harmful patterns
    for pattern in harmful_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return GuardrailFunctionOutput(
                output_info={"is_safe": False, "reason": "Output contains potentially harmful content."},
                tripwire_triggered=True,
            )

    # Output is safe
    return GuardrailFunctionOutput(
        output_info={"is_safe": True, "reason": "Output passed safety checks."},
        tripwire_triggered=False,
    )


# ============================================================================
# SPECIALIZED AGENTS
# ============================================================================

def create_math_tutor_agent(client_name: ClientName = "openai") -> Agent:
    """Create a Math Tutor agent."""
    model = get_model_for_client(client_name)

    agent = Agent(
        name="Math Tutor",
        handoff_description="Expert in mathematics, algebra, calculus, statistics, and problem-solving.",
        instructions="You are a Math Tutor. Help students understand math concepts, solve problems, and explain solutions clearly.",
        model=model,
    )
    return agent


def create_ai_expert_agent(client_name: ClientName = "openai") -> Agent:
    """Create an AI Expert agent."""
    model = get_model_for_client(client_name)

    agent = Agent(
        name="AI Expert",
        handoff_description="Expert in artificial intelligence, machine learning, deep learning, and AI applications.",
        instructions="You are an AI Expert. Explain AI concepts, machine learning algorithms, and help with AI-related questions.",
        model=model,
    )
    return agent


def create_business_specialist_agent(client_name: ClientName = "openai") -> Agent:
    """Create a Business Specialist agent."""
    model = get_model_for_client(client_name)

    agent = Agent(
        name="Business Specialist",
        handoff_description="Expert in business strategy, marketing, finance, and entrepreneurship.",
        instructions="You are a Business Specialist. Provide advice on business strategy, marketing, finance, and entrepreneurship.",
        model=model,
    )
    return agent


def create_triage_agent_with_handoffs(client_name: ClientName = "openai") -> Agent:
    """
    Create a triage agent with handoffs to specialized agents.
    """
    model = get_model_for_client(client_name)

    # Create specialized agents
    math_agent = create_math_tutor_agent(client_name)
    ai_agent = create_ai_expert_agent(client_name)
    business_agent = create_business_specialist_agent(client_name)

    # Create triage agent with handoffs and guardrails
    triage_agent = Agent(
        name="Triage Agent",
        handoff_description="Routes questions to the appropriate specialist agent.",
        instructions="""You determine which specialist should handle the question. Analyze the question and hand it off to the right specialist.""",
        model=model,
        handoffs=[math_agent, ai_agent, business_agent],
        input_guardrails=[InputGuardrail(guardrail_function=check_unsafe_content)],
        output_guardrails=[OutputGuardrail(guardrail_function=check_unsafe_output)],
    )

    return triage_agent


# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

class HandoffResult(BaseModel):
    """Result of agent handoff process."""
    success: bool
    routed_to: str
    final_response: str
    guardrail_passed: bool
    warnings: list[str] = []
    errors: list[str] = []


async def process_with_guardrails_and_handoffs(
    user_input: str,
    client_name: ClientName = "openai"
) -> HandoffResult:
    """
    Process user input with guardrails and agent handoffs.

    Flow:
    1. Input Guardrail checks the input (automatic)
    2. Triage Agent determines which specialist to use
    3. Specialized Agent processes the request
    4. Output Guardrail checks the response (automatic)
    5. Return result
    """
    try:
        print("\n" + "="*60)
        print(f"Processing: {user_input}")
        print("="*60)

        # Setup client
        client = get_client(client_name)

        # For OpenAI, use the full Agents SDK with automatic guardrails
        if client_name == "openai":
            set_default_openai_client(client)

            # Create triage agent with handoffs and guardrails
            triage_agent = create_triage_agent_with_handoffs(client_name)

            print("\n[Running Triage Agent with Handoffs...]")
            result = await Runner.run(triage_agent, user_input)

            print(f"\n[Result Received]")
            print(f"Final Output: {result.final_output}")

            # Determine which agent handled it
            routed_to = "Unknown"
            if hasattr(result, 'agent_name'):
                routed_to = result.agent_name
            else:
                response_lower = result.final_output.lower()
                if any(word in response_lower for word in ['math', 'equation', 'calculate', 'solve']):
                    routed_to = "Math Tutor"
                elif any(word in response_lower for word in ['ai', 'machine learning', 'neural', 'model']):
                    routed_to = "AI Expert"
                elif any(word in response_lower for word in ['business', 'strategy', 'marketing', 'finance']):
                    routed_to = "Business Specialist"
                else:
                    routed_to = "Triage Agent"

            return HandoffResult(
                success=True,
                routed_to=routed_to,
                final_response=result.final_output,
                guardrail_passed=True,
                warnings=[],
                errors=[]
            )

        # For DeepSeek and Gemini, use direct API with manual guardrails
        else:
            print("\n[Step 1: Input Guardrail Check]")
            input_check = await check_unsafe_content(None, None, user_input)
            if input_check.tripwire_triggered:
                print(f"✗ Input blocked: {input_check.output_info['reason']}")
                return HandoffResult(
                    success=False,
                    routed_to="blocked",
                    final_response="Request blocked by safety guardrails.",
                    guardrail_passed=False,
                    warnings=[],
                    errors=[input_check.output_info['reason']]
                )
            print("✓ Input passed guardrail")

            print("\n[Step 2: Route to Specialist]")
            model = get_model_for_client(client_name)
            user_input_lower = user_input.lower()

            if any(word in user_input_lower for word in ['math', 'equation', 'solve', 'calculate', 'algebra']):
                specialist = create_math_tutor_agent(client_name)
                routed_to = "Math Tutor"
            elif any(word in user_input_lower for word in ['ai', 'machine learning', 'neural', 'artificial intelligence']):
                specialist = create_ai_expert_agent(client_name)
                routed_to = "AI Expert"
            elif any(word in user_input_lower for word in ['business', 'marketing', 'strategy', 'finance']):
                specialist = create_business_specialist_agent(client_name)
                routed_to = "Business Specialist"
            else:
                specialist = create_ai_expert_agent(client_name)
                routed_to = "AI Expert"

            print(f"✓ Routed to: {routed_to}")

            print("\n[Step 3: Process Request]")
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": specialist.instructions},
                    {"role": "user", "content": user_input}
                ]
            )
            final_output = response.choices[0].message.content
            print(f"✓ Response received")

            print("\n[Step 4: Output Guardrail Check]")
            output_check = await check_unsafe_output(None, None, final_output)
            if output_check.tripwire_triggered:
                print(f"✗ Output blocked: {output_check.output_info['reason']}")
                return HandoffResult(
                    success=False,
                    routed_to=routed_to,
                    final_response="Response blocked by safety guardrails.",
                    guardrail_passed=False,
                    warnings=[],
                    errors=[output_check.output_info['reason']]
                )
            print("✓ Output passed guardrail")

            return HandoffResult(
                success=True,
                routed_to=routed_to,
                final_response=final_output,
                guardrail_passed=True,
                warnings=[],
                errors=[]
            )

    except Exception as e:
        print(f"\n[Error]: {str(e)}")
        import traceback
        traceback.print_exc()

        # Check if it's a guardrail error
        error_msg = str(e)
        if "guardrail" in error_msg.lower() or "unsafe" in error_msg.lower():
            return HandoffResult(
                success=False,
                routed_to="blocked",
                final_response="Request blocked by safety guardrails.",
                guardrail_passed=False,
                warnings=[],
                errors=[error_msg]
            )

        return HandoffResult(
            success=False,
            routed_to="error",
            final_response="",
            guardrail_passed=False,
            warnings=[],
            errors=[error_msg]
        )


if __name__ == "__main__":
    asyncio.run(demo_guardrails_and_handoffs())
