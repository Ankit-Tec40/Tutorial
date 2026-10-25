"""Comprehensive portfolio capstone projects dataset for the AI Engineering Lab."""

PROJECTS_DATA = [
    {
        "slug": "capstone-1-knowledge-assistant",
        "title": "Capstone 1: Personal AI Knowledge Assistant",
        "badge": "Foundations & RAG",
        "difficulty": "Intermediate",
        "order": 1,
        "description": "An interactive personal knowledge assistant combining vector embeddings, grounded RAG, and document indexing for technical documentation.",
        "objectives": [
            "Ingest Markdown and text documentation into persistent SQLite vector storage",
            "Implement semantic retrieval using cosine similarity and relevance scoring",
            "Generate grounded answers with verifiable source citations",
        ],
        "requirements": [
            "Support uploading .txt and .md technical notes",
            "Reject queries when evidence is insufficient without hallucinating",
            "Expose a clean CLI and REST API for document querying",
        ],
        "architecture_mermaid": (
            "graph TD\n"
            "    User[User Query] --> Embed[Query Embedding]\n"
            "    Embed --> Search[(Vector Store)]\n"
            "    Search -->|Top-3 Matches| Context[Context Assembly]\n"
            "    Context --> GroundedPrompt[Grounded System Prompt]\n"
            "    GroundedPrompt --> LLM[Gemini / Ollama]\n"
            "    LLM --> Answer[Grounded Answer with Citations]"
        ),
        "dependencies": ["flask", "pydantic", "numpy", "requests"],
        "run_instructions_markdown": (
            "### How to run this project:\n"
            "1. Upload your engineering notes via the RAG interface or place `.md` files in `sandbox_fs/`.\n"
            "2. Start the Assistant script:\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe lab_examples/capstone1_assistant.py\n"
            "```\n"
            "3. Ask technical questions and inspect citations."
        ),
        "troubleshooting_markdown": (
            "- If answers state 'Insufficient evidence', check that documents have been indexed.\n"
            "- If using local Ollama, verify `ollama serve` is running."
        ),
        "extension_challenges": [
            "Add Reciprocal Rank Fusion hybrid search for exact error code matching",
            "Implement document tagging and metadata filtering by author or date",
        ],
        "files": [
            {
                "filename": "assistant.py",
                "file_path": "assistant.py",
                "language": "python",
                "is_entry_point": True,
                "content": (
                    "# Personal AI Knowledge Assistant\n"
                    "import os\n"
                    "from app.services.rag.pipeline import RAGPipeline\n\n"
                    "def ask_knowledge_assistant(question: str) -> dict:\n"
                    "    pipeline = RAGPipeline()\n"
                    "    result = pipeline.query_rag(query=question)\n"
                    "    return result\n\n"
                    "if __name__ == '__main__':\n"
                    "    q = 'What are the core principles of AI Engineering?'\n"
                    "    print(f'Query: {q}')\n"
                    "    res = ask_knowledge_assistant(q)\n"
                    "    print(f'Answer:\\n{res[\"answer\"]}')\n"
                )
            }
        ]
    },
    {
        "slug": "capstone-2-tool-using-agent",
        "title": "Capstone 2: Autonomous Tool-Using Research Agent",
        "badge": "Agents & Tools",
        "difficulty": "Advanced",
        "order": 2,
        "description": "A multi-step autonomous agent operating on the ReAct framework with safe tool execution, iteration guards, and human approval for file writes.",
        "objectives": [
            "Decompose complex user goals into intermediate actions and observations",
            "Safely execute mathematical calculations, time queries, and doc searches",
            "Pause execution for human-in-the-loop approval before sensitive file writes",
        ],
        "requirements": [
            "Strict max_iterations guard (default 5) to prevent infinite loops",
            "AST-based safe calculator without unrestricted eval()",
            "Step-by-step execution trace logging",
        ],
        "architecture_mermaid": (
            "sequenceDiagram\n"
            "    autonumber\n"
            "    User->>Agent: Goal: Research topics & save report\n"
            "    Agent->>Tool: search_documents(query)\n"
            "    Tool-->>Agent: Observation: Knowledge excerpts\n"
            "    Agent->>Tool: calculator(math)\n"
            "    Tool-->>Agent: Observation: Math result\n"
            "    Agent->>User: Request Approval to write report.txt\n"
            "    User-->>Agent: Approved\n"
            "    Agent->>Tool: write_sandbox_file(report.txt)\n"
            "    Tool-->>Agent: Observation: File written\n"
            "    Agent-->>User: Final Answer: Report created successfully"
        ),
        "dependencies": ["flask", "pydantic", "requests"],
        "run_instructions_markdown": (
            "### How to run:\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe lab_examples/capstone2_agent.py\n"
            "```"
        ),
        "troubleshooting_markdown": (
            "- Ensure target filenames do not contain path traversal characters (`..`).\n"
            "- Check provider quota if using Gemini."
        ),
        "extension_challenges": [
            "Add Web search tool integration with rate limiting",
            "Implement multi-agent consensus verification before final answer",
        ],
        "files": [
            {
                "filename": "research_agent.py",
                "file_path": "research_agent.py",
                "language": "python",
                "is_entry_point": True,
                "content": (
                    "# Autonomous Research Agent\n"
                    "from app.services.agents.framework import CustomAgent\n\n"
                    "def run_agent_job(goal: str):\n"
                    "    agent = CustomAgent(max_iterations=4)\n"
                    "    return agent.run(goal=goal)\n\n"
                    "if __name__ == '__main__':\n"
                    "    goal = 'Calculate 144 * 12 and retrieve current UTC time.'\n"
                    "    res = run_agent_job(goal)\n"
                    "    print('Status:', res['status'])\n"
                    "    print('Final Answer:', res['final_answer'])\n"
                )
            }
        ]
    },
    {
        "slug": "capstone-3-mcp-toolkit",
        "title": "Capstone 3: MCP Server and Client Toolkit",
        "badge": "Model Context Protocol",
        "difficulty": "Advanced",
        "order": 3,
        "description": "Standardized Model Context Protocol server exposing verified tools, resources, and prompts with dynamic client schema discovery.",
        "objectives": [
            "Expose tools and resources compliant with the official MCP 2.x specification",
            "Build an interactive client that discovers tools and invokes them with timing",
            "Implement sandboxed filesystem boundary verification",
        ],
        "requirements": [
            "Support stdio transport for local agent orchestration",
            "Enforce JSON-RPC 2.0 schema validation on all inputs",
            "Track tool execution latency in milliseconds",
        ],
        "architecture_mermaid": (
            "graph LR\n"
            "    HostClient[MCP Host / Client] -->|stdio JSON-RPC| MCPServer[lab-mcp-server]\n"
            "    MCPServer --> Tool1[calculator]\n"
            "    MCPServer --> Tool2[notes_search]\n"
            "    MCPServer --> Tool3[approved_dir_listing]\n"
            "    MCPServer --> Resource1[resource://docs/intro]"
        ),
        "dependencies": ["mcp", "pydantic", "anyio"],
        "run_instructions_markdown": (
            "### How to run:\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe mcp_servers/lab_mcp_server.py\n"
            "```"
        ),
        "troubleshooting_markdown": (
            "- Ensure the official `mcp` package is installed (`pip install mcp`).\n"
            "- On Windows, handle stdio carriage returns cleanly."
        ),
        "extension_challenges": [
            "Add streamable HTTP transport for remote MCP servers",
            "Implement dynamic prompt templates via MCP prompts/list",
        ],
        "files": [
            {
                "filename": "mcp_runner.py",
                "file_path": "mcp_runner.py",
                "language": "python",
                "is_entry_point": True,
                "content": (
                    "# MCP Client Discovery\n"
                    "from app.services.mcp.service import MCPManagerService\n\n"
                    "service = MCPManagerService()\n"
                    "tools = service.list_tools()\n"
                    "print(f'Discovered {len(tools)} MCP tools:')\n"
                    "for t in tools:\n"
                    "    print(f'- {t[\"name\"]}: {t[\"description\"]}')\n"
                )
            }
        ]
    },
    {
        "slug": "capstone-4-gemini-ollama-benchmark",
        "title": "Capstone 4: Gemini-vs-Ollama Benchmarking Suite",
        "badge": "Evaluation & Metrics",
        "difficulty": "Intermediate",
        "order": 4,
        "description": "A repeatable evaluation framework that tests identical prompts across Google Gemini and local Ollama, comparing latency, tokens, and output quality.",
        "objectives": [
            "Run side-by-side prompt benchmarks across cloud and local models",
            "Measure tokens per second and round-trip latency in milliseconds",
            "Assess output conformity to JSON schemas and required keywords",
        ],
        "requirements": [
            "Do not fabricate token metrics; clearly mark unavailable metrics",
            "Gracefully notify if Ollama or Gemini is unconfigured",
            "Export benchmark reports as JSON or CSV",
        ],
        "architecture_mermaid": (
            "graph TD\n"
            "    BenchmarkRunner[Benchmark Test Suite] --> Prompt[Standardized Prompts]\n"
            "    Prompt --> Gemini[Gemini 2.5 Flash]\n"
            "    Prompt --> Ollama[Ollama Llama 3.2]\n"
            "    Gemini --> M1[Latency: 450ms, Tokens: 120]\n"
            "    Ollama --> M2[Latency: 1200ms, Tokens: 118]\n"
            "    M1 --> Comparison[Comparison Table & Pass Rate]\n"
            "    M2 --> Comparison"
        ),
        "dependencies": ["google-genai", "requests", "pydantic"],
        "run_instructions_markdown": (
            "### How to run:\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe lab_examples/capstone4_benchmark.py\n"
            "```"
        ),
        "troubleshooting_markdown": (
            "- If local inference is slow, check available RAM and select a smaller model like `llama3.2:1b`."
        ),
        "extension_challenges": [
            "Add automated cost estimation per 1M tokens for Gemini cloud models",
            "Implement semantic similarity comparison between Gemini and Ollama responses",
        ],
        "files": [
            {
                "filename": "benchmark.py",
                "file_path": "benchmark.py",
                "language": "python",
                "is_entry_point": True,
                "content": (
                    "# Provider Benchmark Runner\n"
                    "import time\n"
                    "from app.services.providers.factory import get_provider\n\n"
                    "def run_benchmark(prompt: str):\n"
                    "    results = {}\n"
                    "    for p_name in ['gemini', 'ollama']:\n"
                    "        try:\n"
                    "            provider = get_provider(p_name)\n"
                    "            resp = provider.generate(prompt=prompt)\n"
                    "            results[p_name] = {\n"
                    "                'model': resp.model,\n"
                    "                'latency_ms': resp.latency_ms,\n"
                    "                'tokens': resp.total_tokens,\n"
                    "                'preview': resp.content[:100] + '...'\n"
                    "            }\n"
                    "        except Exception as e:\n"
                    "            results[p_name] = {'error': str(e)}\n"
                    "    return results\n\n"
                    "if __name__ == '__main__':\n"
                    "    res = run_benchmark('Explain vector embeddings in 1 sentence.')\n"
                    "    print('Benchmark Results:', res)\n"
                )
            }
        ]
    },
    {
        "slug": "capstone-5-end-to-end-agentic-rag",
        "title": "Capstone 5: End-to-End Agentic RAG System",
        "badge": "Mastery Capstone",
        "difficulty": "Advanced",
        "order": 5,
        "description": "A flagship application uniting vector search, custom ReAct agent loops, safe calculator tools, and MCP discovery into a complete AI system.",
        "objectives": [
            "Combine semantic retrieval with dynamic multi-step agent reasoning",
            "Allow the agent to autonomously decide when to search documents vs invoke tools",
            "Enforce strict human approval gates before saving synthesized briefs to the sandbox",
        ],
        "requirements": [
            "Unified agent loop with document search and arithmetic tools",
            "Exportable workspace files and execution traces",
            "Zero hallucination on unsupported questions",
        ],
        "architecture_mermaid": (
            "graph TD\n"
            "    Goal[Complex User Request] --> Agent[Custom ReAct Agent]\n"
            "    Agent --> Decider{Requires External Data?}\n"
            "    Decider -->|Knowledge Query| RAG[RAG Search Tool]\n"
            "    Decider -->|Calculation| Calc[Safe AST Calculator]\n"
            "    Decider -->|System Time| Time[Current Time Tool]\n"
            "    RAG --> Synthesize[Observation Synthesis]\n"
            "    Calc --> Synthesize\n"
            "    Time --> Synthesize\n"
            "    Synthesize --> ApprovalGate{Action: Save File?}\n"
            "    ApprovalGate -->|User Approves| Write[Write to Sandbox]\n"
            "    Write --> FinalAnswer[Deliver Final Verifiable Brief]"
        ),
        "dependencies": ["flask", "pydantic", "google-genai", "requests", "numpy", "mcp"],
        "run_instructions_markdown": (
            "### How to run:\n"
            "1. Upload reference documents via the RAG Lab tab.\n"
            "2. Open the Agent Lab tab in your browser or run the script:\n"
            "```powershell\n"
            ".\\.venv\\Scripts\\python.exe lab_examples/capstone5_agentic_rag.py\n"
            "```\n"
            "3. Observe step-by-step reasoning in real time."
        ),
        "troubleshooting_markdown": (
            "- If the agent terminates early, check the `max_iterations` setting.\n"
            "- If file write is rejected, verify that human approval was granted."
        ),
        "extension_challenges": [
            "Integrate an automated citation verifier checking each sentence against source chunks",
            "Add multi-user isolation for enterprise sandbox directories",
        ],
        "files": [
            {
                "filename": "agentic_rag.py",
                "file_path": "agentic_rag.py",
                "language": "python",
                "is_entry_point": True,
                "content": (
                    "# Flagship Agentic RAG System\n"
                    "from app.services.agents.framework import CustomAgent\n\n"
                    "def execute_flagship_agent(goal: str):\n"
                    "    agent = CustomAgent(max_iterations=5)\n"
                    "    return agent.run(goal=goal)\n\n"
                    "if __name__ == '__main__':\n"
                    "    goal = 'Search the knowledge base for RAG concepts and calculate 128 * 8.'\n"
                    "    result = execute_flagship_agent(goal)\n"
                    "    print('Status:', result['status'])\n"
                    "    print('Answer:', result['final_answer'])\n"
                )
            }
        ]
    }
]
