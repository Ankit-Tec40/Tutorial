# AI Engineering Lab 🧠⚡

A full-stack, production-minded educational web application built with **Flask**, **Google Gemini API**, **Ollama**, and the official **Model Context Protocol (MCP)** SDK.

Learn modern AI engineering through interactive lessons, working code playgrounds, grounded RAG pipelines, autonomous multi-step agents, and real capstone implementations.

---

## 🌟 Key Features

1. **Dual AI Provider Architecture**:
   - **Google Gemini API**: Cloud inference via the official `google-genai` SDK supporting streaming, JSON mode, and function calling.
   - **Ollama**: 100% private local LLM inference (e.g., Llama 3.2) without external network calls or cloud costs.
   - **Dual-Model Comparator**: Side-by-side prompt benchmarking comparing latency, tokens, and output quality.
2. **Complete 15-Module Curriculum**:
   - 15 seeded modules from Python and Token Foundations to Grounded RAG, Autonomous ReAct Agents, MCP, Multimodal AI, and Evaluation Safety.
   - Every lesson includes learning objectives, prerequisites, concept explanations, Mermaid architecture diagrams, working code, runnable playgrounds, hands-on exercises, and graded quizzes.
3. **Interactive AI Laboratories**:
   - **Document RAG Lab**: Ingest `.txt`, `.md`, `.py` documents into a persistent SQLite vector store. Queries are grounded strictly in retrieved passages with bracketed citations `[1]`, `[2]`, or fallback to *"Insufficient evidence"*.
   - **Tool Calling Lab**: Safe function calling with AST-based arithmetic and schema inspection.
   - **Agentic AI Workbench**: Autonomous ReAct agent loops with live execution traces and **Human-in-the-Loop approval** before sensitive actions (such as file writes).
   - **MCP Visual Inspector**: Discover tools and resources from an MCP server using the official Model Context Protocol 2.x SDK.
   - **Evaluation Runner**: Golden test dataset runner comparing pass rate, required keyword retention, and round-trip latency.
4. **Portfolio-Grade Capstone Workspaces**:
   - 5 flagship capstone projects with full requirements, architecture diagrams, runnable CLI scripts, and clean one-click ZIP export.
5. **Modern Developer Interface**:
   - Dark and light themes, collapsible sidebar navigation, search modal (`Ctrl+K`), live status pills, and progress tracking.

---

## 🚀 Quickstart Guide (Windows & PowerShell)

### 1. Prerequisites
- **Python 3.12+** installed (`python --version` or `py -3.12 --version`).
- **Ollama** (optional, for local offline inference): [ollama.com](https://ollama.com/).

### 2. Virtual Environment & Dependencies

Open PowerShell in the project directory:

```powershell
# Create virtual environment
py -3.12 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install -r requirements.txt
```

*(Linux/macOS: `source .venv/bin/activate`)*

### 3. Environment Configuration

Copy the example configuration file:

```powershell
Copy-Item .env.example .env
```

Open `.env` in your editor and optionally add your **Google Gemini API Key**:
```dotenv
FLASK_SECRET_KEY=dev-secret-key-change-me
DATABASE_URL=sqlite:///instance/ai_engineering_lab.db

GEMINI_API_KEY=your_google_ai_studio_api_key_here
GEMINI_MODEL=gemini-2.5-flash

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

> **Note:** The application works completely without a Gemini key if you use local Ollama!

### 4. (Optional) Local Ollama Setup

If you want to use local open-weights models without API charges:
```powershell
# Pull the recommended lightweight 3B model
ollama pull llama3.2

# Verify installed models
ollama list
```

Ensure Ollama is running in the background (`ollama serve`).

### 5. Initialize Database & Seed Curriculum

Run the built-in Flask CLI commands to create database tables and populate the 15 learning modules and capstones:

```powershell
# Initialize SQLite database tables
python -m flask --app wsgi.py init-db

# Seed curriculum, quizzes, and capstone projects
python -m flask --app wsgi.py seed-lessons
```

### 6. Start the Application

```powershell
python wsgi.py
```

Open your browser to: **[http://localhost:5000](http://localhost:5000)**.

---

## 🧪 Running Automated Tests

Run the complete 18-test pytest suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

All tests run against an in-memory SQLite database and mocked provider endpoints, requiring **no Gemini API key** or network access.

---

## 📂 Project Architecture

```text
ai-engineering-lab/
├── app/
│   ├── __init__.py               # Flask application factory & CLI commands
│   ├── config.py                 # Configuration classes & path management
│   ├── extensions.py             # SQLAlchemy & Migrate instances
│   ├── models/                   # Database schemas
│   │   ├── module.py             # LearningModule & Lesson models
│   │   ├── progress.py           # LessonProgress, QuizQuestion, LabRun
│   │   ├── project.py            # Project & ProjectFile models
│   │   ├── chat.py               # ChatSession & ChatMessage models
│   │   ├── setting.py            # AppSetting key-value store
│   │   ├── evaluation.py         # EvaluationRun benchmark history
│   │   └── rag.py                # RAGDocument & RAGChunk vector models
│   ├── routes/                   # Blueprints
│   │   ├── main.py               # Dashboard, search, health check
│   │   ├── lessons.py            # Lesson views, quiz grading, lab runner
│   │   ├── chat.py               # Single & dual-model chat with SSE streaming
│   │   ├── rag.py                # Document upload, chunking, grounded search
│   │   ├── tools.py              # Tool calling laboratory
│   │   ├── agents.py             # ReAct loop & human approval gate
│   │   ├── mcp.py                # Model Context Protocol inspector
│   │   ├── projects.py           # Capstones & ZIP export
│   │   ├── evaluations.py        # Benchmark suite runner
│   │   └── settings.py           # Provider configuration & connectivity probes
│   ├── services/                 # Core AI business logic
│   │   ├── providers/            # Base, Gemini, Ollama, & Factory
│   │   ├── embeddings/           # Cosine similarity & semantic vectorizer
│   │   ├── rag/                  # Document parsing, chunking, grounded synthesis
│   │   ├── agents/               # ReAct framework & safe tools
│   │   ├── mcp/                  # MCP server manager & client discovery
│   │   └── execution/            # Server-side safe lab dispatcher
│   ├── lessons/                  # Curriculum datasets & seeders
│   ├── templates/                # Jinja2 templates (dashboard, lesson, labs)
│   └── static/                   # Custom CSS design system & JavaScript ES modules
├── lab_examples/                 # Standalone runnable capstone CLI scripts
├── mcp_servers/                  # Standalone runnable stdio MCP server
├── tests/                        # Pytest automated test suite
├── Dockerfile                    # Containerization build
├── docker-compose.yml            # Multi-container orchestration
├── wsgi.py                       # WSGI entrypoint
└── README.md
```

---

## 🔒 Security & Sandboxing Architecture

1. **Zero Host Execution**:
   - The playground **never** executes arbitrary Python source strings via `eval()` or `exec()` on the host process.
   - Lab examples dispatch to pre-registered server-side handlers with strict Pydantic argument validation.
2. **Safe Calculator**:
   - Mathematical expressions are parsed strictly through Python's `ast` (Abstract Syntax Tree), ensuring only arithmetic operators (`+`, `-`, `*`, `/`) can run.
3. **Sandbox Directory Boundary**:
   - File actions are strictly restricted to `sandbox_fs/`. Path traversal (`../`) attempts are detected and rejected.
4. **Human-in-the-Loop Approval**:
   - Sensitive tools (e.g. `write_sandbox_file`) halt agent loops with status `awaiting_approval` until explicitly approved via the UI modal.
5. **Secret Protection**:
   - API keys are never stored in the database or exposed to HTML/JavaScript.
   - Capstone ZIP exports exclude `.env` files and SQLite databases automatically.

---

## 🛠️ Adding New Lessons or Model Providers

### Adding a Lesson:
1. Open `app/lessons/curriculum_data.py`.
2. Add a new lesson dictionary to the appropriate module in `MODULES_DATA` with the 19 standard fields.
3. Re-run `python -m flask --app wsgi.py seed-lessons`.

### Adding a Provider:
1. Create a new subclass of `BaseLLMProvider` in `app/services/providers/your_provider.py`.
2. Implement `test_connection()`, `generate()`, `stream_chat()`, and `list_models()`.
3. Register it in `app/services/providers/factory.py`.

---

## 🐳 Docker Deployment

To run using Docker Compose:

```bash
docker compose up -d
```

Access the lab at `http://localhost:5000`.
