"""Capstone 5: End-to-End Agentic RAG System CLI.

Usage:
    python lab_examples/capstone5_agentic_rag.py
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
        print("  Flagship End-to-End Agentic RAG System")
        print("=" * 60)

        agent = CustomAgent(max_iterations=5)
        goal = "Search the knowledge base for RAG concepts, calculate 256 * 16, and provide a synthesized summary."
        print(f"\nAutonomous Goal: {goal}\n")

        res = agent.run(goal=goal)
        print("Status:", res["status"])
        print(f"Total Steps Executed: {res.get('total_steps', len(res.get('trace', [])))}")
        print("\nFinal Answer:\n", res.get("final_answer"))


if __name__ == "__main__":
    main()
