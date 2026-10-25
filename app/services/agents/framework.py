import json
import time
import re
import logging
from typing import Dict, Any, List, Optional
from app.services.agents.tools import TOOL_REGISTRY
from app.services.providers.factory import get_provider

logger = logging.getLogger(__name__)


class AgentTraceStep:
    def __init__(self, step_number: int, thought: str = "", action: Optional[str] = None, 
                 action_input: Optional[Dict[str, Any]] = None, observation: Optional[Any] = None):
        self.step_number = step_number
        self.thought = thought
        self.action = action
        self.action_input = action_input or {}
        self.observation = observation
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "action_input": self.action_input,
            "observation": self.observation,
            "timestamp": self.timestamp,
        }


class CustomAgent:
    """A transparent, multi-step ReAct agent engine supporting human approval and execution traces."""

    def __init__(
        self,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        max_iterations: int = 5,
        allowed_tools: Optional[List[str]] = None,
    ):
        self.provider = get_provider(provider_name=provider_name, model_name=model_name)
        self.max_iterations = max_iterations
        self.allowed_tools = allowed_tools or list(TOOL_REGISTRY.keys())
        self.trace: List[AgentTraceStep] = []
        self.status = "idle"  # idle, running, awaiting_approval, completed, error
        self.pending_approval: Optional[Dict[str, Any]] = None

    def _build_system_prompt(self) -> str:
        tools_desc = []
        for name in self.allowed_tools:
            if name in TOOL_REGISTRY:
                info = TOOL_REGISTRY[name]
                tools_desc.append(f"- **{name}**: {info['description']}\n  Schema: {json.dumps(info['parameters'])}")

        tools_str = "\n".join(tools_desc)

        return (
            "You are an autonomous AI Agent operating in an AI Engineering Lab.\n"
            "You have access to the following approved tools:\n\n"
            f"{tools_str}\n\n"
            "### Execution Format:\n"
            "To solve the goal, reason step-by-step using this strict format:\n\n"
            "Thought: <Your internal reasoning and plan for what to do next>\n"
            "Action: <Name of tool to use, must match one of the approved tools above, or 'Final Answer'>\n"
            "Action Input: <JSON object containing arguments for the tool, or empty object {}>\n\n"
            "When you have enough information to solve the user's goal, conclude with:\n"
            "Thought: I now have all necessary information to answer.\n"
            "Action: Final Answer\n"
            "Action Input: {\"answer\": \"Your comprehensive final response here.\"}\n\n"
            "Important Rules:\n"
            "1. Only use tools from the provided list.\n"
            "2. Ensure Action Input is valid JSON.\n"
            "3. Do not assume tool results; wait for the Observation after each tool call.\n"
        )

    def _parse_llm_step(self, text: str) -> Dict[str, Any]:
        """Extracts Thought, Action, and Action Input from model generation."""
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r"Action:\s*([^\n]+)", text, re.IGNORECASE)
        input_match = re.search(r"Action Input:\s*(\{.*\}|\[.*\]|[^\n]+)", text, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else text.strip()
        action = action_match.group(1).strip() if action_match else None
        action_input = {}

        if input_match:
            raw_input = input_match.group(1).strip()
            try:
                # Find outermost JSON object
                json_start = raw_input.find("{")
                json_end = raw_input.rfind("}")
                if json_start != -1 and json_end != -1:
                    action_input = json.loads(raw_input[json_start:json_end+1])
                else:
                    action_input = json.loads(raw_input)
            except Exception:
                action_input = {"raw": raw_input}

        return {
            "thought": thought,
            "action": action,
            "action_input": action_input,
        }

    def run(
        self,
        goal: str,
        human_approval_granted: bool = False,
        approved_action: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs the agent loop until completion, approval request, or iteration limit."""
        start_time = time.perf_counter()
        system_prompt = self._build_system_prompt()
        self.status = "running"

        conversation_history = [
            f"Goal: {goal}\n\nPlease proceed with your first step."
        ]

        # Handle resumed run after human approval
        if human_approval_granted and approved_action:
            tool_name = approved_action.get("action")
            tool_args = approved_action.get("action_input", {})
            if tool_name in TOOL_REGISTRY:
                handler = TOOL_REGISTRY[tool_name]["handler"]
                observation = handler(**tool_args)
                step = AgentTraceStep(
                    step_number=len(self.trace) + 1,
                    thought="Resuming execution following explicit user approval.",
                    action=tool_name,
                    action_input=tool_args,
                    observation=observation,
                )
                self.trace.append(step)
                conversation_history.append(
                    f"Observation from {tool_name}: {json.dumps(observation)}"
                )

        final_answer = None

        for iteration in range(1, self.max_iterations + 1):
            prompt = "\n\n".join(conversation_history)

            try:
                response = self.provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.2,
                )
                parsed = self._parse_llm_step(response.content)
            except Exception as e:
                self.status = "error"
                return {
                    "goal": goal,
                    "status": "error",
                    "error": str(e),
                    "trace": [s.to_dict() for s in self.trace],
                    "final_answer": None,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                }

            thought = parsed["thought"]
            action = parsed["action"]
            action_input = parsed["action_input"]

            # Check if agent has reached Final Answer
            if action and ("final answer" in action.lower() or action.lower() == "final_answer"):
                final_answer = action_input.get("answer") if isinstance(action_input, dict) else str(action_input)
                if not final_answer:
                    final_answer = thought

                self.trace.append(AgentTraceStep(
                    step_number=iteration,
                    thought=thought,
                    action="Final Answer",
                    action_input=action_input,
                    observation="Execution finished successfully.",
                ))
                self.status = "completed"
                break

            # If no action was recognized, check if model simply answered directly
            if not action or action not in self.allowed_tools:
                final_answer = response.content
                self.trace.append(AgentTraceStep(
                    step_number=iteration,
                    thought=thought,
                    action="Direct Response",
                    action_input={},
                    observation=final_answer,
                ))
                self.status = "completed"
                break

            # Sensitive Action Approval Gate
            tool_meta = TOOL_REGISTRY.get(action, {})
            if tool_meta.get("is_sensitive", False) and not human_approval_granted:
                self.status = "awaiting_approval"
                self.pending_approval = {
                    "action": action,
                    "action_input": action_input,
                    "description": f"Agent is requesting to execute sensitive action: '{action}' with parameters: {json.dumps(action_input)}",
                }
                self.trace.append(AgentTraceStep(
                    step_number=iteration,
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation="PAUSED: Awaiting user human-in-the-loop approval before executing.",
                ))
                return {
                    "goal": goal,
                    "status": "awaiting_approval",
                    "pending_approval": self.pending_approval,
                    "trace": [s.to_dict() for s in self.trace],
                    "final_answer": None,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                }

            # Execute tool safely
            handler = tool_meta.get("handler")
            try:
                if isinstance(action_input, dict):
                    obs = handler(**action_input)
                else:
                    obs = handler(action_input)
            except Exception as e:
                obs = {"error": f"Tool execution error: {str(e)}"}

            self.trace.append(AgentTraceStep(
                step_number=iteration,
                thought=thought,
                action=action,
                action_input=action_input,
                observation=obs,
            ))

            conversation_history.append(
                f"Thought: {thought}\nAction: {action}\nAction Input: {json.dumps(action_input)}\nObservation: {json.dumps(obs)}"
            )

        if not final_answer:
            final_answer = "Agent reached maximum iteration limit without finding an explicit final answer."
            self.status = "max_iterations_reached"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "goal": goal,
            "status": self.status,
            "final_answer": final_answer,
            "trace": [s.to_dict() for s in self.trace],
            "total_steps": len(self.trace),
            "latency_ms": round(elapsed_ms, 2),
            "provider": self.provider.name,
            "model": self.provider.model_name,
        }
