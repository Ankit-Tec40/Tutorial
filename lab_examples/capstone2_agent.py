"""Capstone 2: Autonomous Tool-Using Research Agent CLI.

Usage:
    python lab_examples/capstone2_agent.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.services.agents.framework import CustomAgent


def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("  Autonomous Tool-Using Research Agent (ReAct)")
        print("=" * 60)

        agent = CustomAgent(max_iterations=4)
        goal = "Find the current UTC time and calculate 144 * 12."
        print(f"\nGoal: {goal}\n")

        res = agent.run(goal=goal)
        print("Status:", res["status"])
        print("Total Steps:", len(res["trace"]))
        print("\nTrace Timeline:")
        for step in res["trace"]:
            print(f"  Step {step['step_number']}: Thought: {step['thought']}")
            print(f"          Action:  {step['action']}({step['action_input']})")
            print(f"          Obs:     {step['observation']}\n")

        if res.get("error"):
            print(f"Error / Notice: {res['error']}")
        print("Final Answer:\n", res["final_answer"])


if __name__ == "__main__":
    main()
