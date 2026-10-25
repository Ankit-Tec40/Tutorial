"""Capstone 1: Personal AI Knowledge Assistant CLI.

Usage:
    python lab_examples/capstone1_assistant.py
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.services.rag.pipeline import RAGPipeline


def main():
    app = create_app()
    with app.app_context():
        pipeline = RAGPipeline()
        print("=" * 60)
        print("  Personal AI Knowledge Assistant (RAG)")
        print("=" * 60)

        query = "What are the core principles of AI Engineering?"
        print(f"\nQuerying knowledge base: '{query}'\n")

        res = pipeline.query_rag(query=query)
        print(f"Grounded Answer:\n{res['answer']}\n")
        print(f"Latency: {res['latency_ms']} ms | Provider: {res['provider']}")

        if res.get("sources"):
            print("\nSources Cited:")
            for s in res["sources"]:
                print(f"  [{s['citation_index']}] {s['filename']} (Score: {s['score']})")


if __name__ == "__main__":
    main()
