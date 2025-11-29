"""Unified KakoAI ReAct agent wiring available tools."""
from __future__ import annotations

import dspy

from backend.src.tools.bom import perform_bom_extraction


class KakoAgentSignature(dspy.Signature):
    """You are KakoAI: solve the user's request by reasoning and calling tools when useful."""

    user_query: str = dspy.InputField(
        desc="Natural-language task or question to solve; include any specifics such as file paths or part numbers."
    )
    process_result: str = dspy.OutputField(
        desc="Natural-language summary of the reasoning steps and tool results."
    )


TOOLBOX = [
    perform_bom_extraction,
    # TODO: Add other tools here
]


class KakoAgent:
    """Thin wrapper around the unified ReAct agent."""

    def __init__(self) -> None:
        self.agent = dspy.ReAct(KakoAgentSignature, tools=TOOLBOX)

    def __call__(self, user_query: str) -> dspy.Prediction:
        """Invoke the agent with a natural-language request and return the ReAct prediction."""
        return self.agent(user_query=user_query)
