"""Capstone 4: Gemini-vs-Ollama Benchmarking Suite CLI.

Usage:
    python lab_examples/capstone4_benchmark.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.services.providers.factory import get_provider


def main():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("  Gemini-vs-Ollama Benchmarking Suite")
        print("=" * 60)

        prompt = "Explain why Retrieval-Augmented Generation reduces hallucination in 2 sentences."
        print(f"\nBenchmark Prompt: '{prompt}'\n")

        for p_name in ["gemini", "ollama"]:
            print(f"Testing Provider: {p_name.upper()}...")
            try:
                prov = get_provider(p_name)
                resp = prov.generate(prompt=prompt, temperature=0.2)
                print(f"  Model:   {resp.model}")
                print(f"  Latency: {resp.latency_ms} ms")
                print(f"  Tokens:  {resp.total_tokens or 'N/A'}")
                print(f"  Output:  {resp.content.strip()}\n")
            except Exception as e:
                print(f"  Status:  Unavailable ({str(e)})\n")


if __name__ == "__main__":
    main()
