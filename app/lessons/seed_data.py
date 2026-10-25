import logging
from app.extensions import db
from app.models.module import LearningModule, Lesson
from app.models.progress import QuizQuestion
from app.models.project import Project, ProjectFile
from app.models.setting import AppSetting
from app.models.rag import RAGDocument, RAGChunk
from app.lessons.curriculum_data import MODULES_DATA
from app.lessons.projects_data import PROJECTS_DATA
from app.services.embeddings.service import EmbeddingService
from app.services.rag.pipeline import chunk_text

logger = logging.getLogger(__name__)


def seed_database():
    """Seeds the curriculum, quizzes, projects, initial settings, and sample RAG documents."""
    logger.info("Starting database seeding...")

    # 1. Seed Curriculum Modules and Lessons
    for m_data in MODULES_DATA:
        module = LearningModule.query.filter_by(slug=m_data["slug"]).first()
        if not module:
            module = LearningModule(
                slug=m_data["slug"],
                title=m_data["title"],
                description=m_data["description"],
                icon=m_data.get("icon", "bi-journal-code"),
                order=m_data["order"],
                estimated_hours=m_data.get("estimated_hours", 2.0),
            )
            db.session.add(module)
            db.session.flush()
        else:
            module.title = m_data["title"]
            module.description = m_data["description"]
            module.icon = m_data.get("icon", "bi-journal-code")
            module.order = m_data["order"]
            module.estimated_hours = m_data.get("estimated_hours", 2.0)

        # Seed Lessons
        for l_data in m_data.get("lessons", []):
            lesson = Lesson.query.filter_by(slug=l_data["slug"]).first()
            if not lesson:
                lesson = Lesson(
                    module_id=module.id,
                    slug=l_data["slug"],
                    title=l_data["title"],
                    summary=l_data["summary"],
                    order=l_data["order"],
                    estimated_minutes=l_data.get("estimated_minutes", 30),
                    prerequisites=l_data.get("prerequisites", []),
                    objectives=l_data.get("objectives", []),
                    explanation_markdown=l_data["explanation_markdown"],
                    real_world_use_cases=l_data.get("real_world_use_cases", []),
                    mermaid_diagram=l_data.get("mermaid_diagram", ""),
                    walkthrough_markdown=l_data.get("walkthrough_markdown", ""),
                    code_example=l_data["code_example"],
                    code_language=l_data.get("code_language", "python"),
                    code_explanation_markdown=l_data.get("code_explanation_markdown", ""),
                    default_parameters=l_data.get("default_parameters", {}),
                    expected_output=l_data.get("expected_output", ""),
                    common_errors_markdown=l_data.get("common_errors_markdown", ""),
                    exercise_prompt=l_data.get("exercise_prompt", ""),
                    exercise_starter_code=l_data.get("exercise_starter_code", ""),
                    exercise_hint=l_data.get("exercise_hint", ""),
                    exercise_solution=l_data.get("exercise_solution", ""),
                    challenge_task=l_data.get("challenge_task", ""),
                    key_takeaways=l_data.get("key_takeaways", []),
                    doc_links=l_data.get("doc_links", []),
                    lab_id=l_data.get("lab_id"),
                )
                db.session.add(lesson)
                db.session.flush()
            else:
                lesson.module_id = module.id
                lesson.title = l_data["title"]
                lesson.summary = l_data["summary"]
                lesson.order = l_data["order"]
                lesson.estimated_minutes = l_data.get("estimated_minutes", 30)
                lesson.prerequisites = l_data.get("prerequisites", [])
                lesson.objectives = l_data.get("objectives", [])
                lesson.explanation_markdown = l_data["explanation_markdown"]
                lesson.real_world_use_cases = l_data.get("real_world_use_cases", [])
                lesson.mermaid_diagram = l_data.get("mermaid_diagram", "")
                lesson.walkthrough_markdown = l_data.get("walkthrough_markdown", "")
                lesson.code_example = l_data["code_example"]
                lesson.code_language = l_data.get("code_language", "python")
                lesson.code_explanation_markdown = l_data.get("code_explanation_markdown", "")
                lesson.default_parameters = l_data.get("default_parameters", {})
                lesson.expected_output = l_data.get("expected_output", "")
                lesson.common_errors_markdown = l_data.get("common_errors_markdown", "")
                lesson.exercise_prompt = l_data.get("exercise_prompt", "")
                lesson.exercise_starter_code = l_data.get("exercise_starter_code", "")
                lesson.exercise_hint = l_data.get("exercise_hint", "")
                lesson.exercise_solution = l_data.get("exercise_solution", "")
                lesson.challenge_task = l_data.get("challenge_task", "")
                lesson.key_takeaways = l_data.get("key_takeaways", [])
                lesson.doc_links = l_data.get("doc_links", [])
                lesson.lab_id = l_data.get("lab_id")

            # Seed Quiz Questions
            QuizQuestion.query.filter_by(lesson_id=lesson.id).delete()
            for q_data in l_data.get("quizzes", []):
                q = QuizQuestion(
                    lesson_id=lesson.id,
                    question_text=q_data["question_text"],
                    options=q_data["options"],
                    correct_index=q_data["correct_index"],
                    explanation=q_data["explanation"],
                )
                db.session.add(q)

    # 2. Seed Capstone Projects
    for p_data in PROJECTS_DATA:
        project = Project.query.filter_by(slug=p_data["slug"]).first()
        if not project:
            project = Project(
                slug=p_data["slug"],
                title=p_data["title"],
                badge=p_data.get("badge", "Capstone"),
                difficulty=p_data.get("difficulty", "Intermediate"),
                order=p_data.get("order", 1),
                description=p_data["description"],
                objectives=p_data.get("objectives", []),
                requirements=p_data.get("requirements", []),
                architecture_mermaid=p_data.get("architecture_mermaid", ""),
                dependencies=p_data.get("dependencies", []),
                run_instructions_markdown=p_data.get("run_instructions_markdown", ""),
                troubleshooting_markdown=p_data.get("troubleshooting_markdown", ""),
                extension_challenges=p_data.get("extension_challenges", []),
                status="not_started",
            )
            db.session.add(project)
            db.session.flush()
        else:
            project.title = p_data["title"]
            project.badge = p_data.get("badge", "Capstone")
            project.difficulty = p_data.get("difficulty", "Intermediate")
            project.order = p_data.get("order", 1)
            project.description = p_data["description"]
            project.objectives = p_data.get("objectives", [])
            project.requirements = p_data.get("requirements", [])
            project.architecture_mermaid = p_data.get("architecture_mermaid", "")
            project.dependencies = p_data.get("dependencies", [])
            project.run_instructions_markdown = p_data.get("run_instructions_markdown", "")
            project.troubleshooting_markdown = p_data.get("troubleshooting_markdown", "")
            project.extension_challenges = p_data.get("extension_challenges", [])

        # Seed Project Files
        ProjectFile.query.filter_by(project_id=project.id).delete()
        for f_data in p_data.get("files", []):
            pf = ProjectFile(
                project_id=project.id,
                filename=f_data["filename"],
                file_path=f_data.get("file_path", f_data["filename"]),
                language=f_data.get("language", "python"),
                is_entry_point=f_data.get("is_entry_point", False),
                content=f_data["content"],
            )
            db.session.add(pf)

    # 3. Seed Starter RAG Document
    if not RAGDocument.query.first():
        starter_text = (
            "AI Engineering Core Principles:\n\n"
            "1. Grounded Generation: Large language models generate fluent prose but can fabricate facts. "
            "In production, models must be grounded using Retrieval-Augmented Generation (RAG) with source citations.\n\n"
            "2. Tool Calling Safety: Models emit structured requests to run tools, but host applications must strictly "
            "validate inputs and enforce sandboxes. Never execute unvalidated model code on host servers.\n\n"
            "3. Agent Loops: An AI agent operates in an iterative ReAct (Reasoning + Acting) loop. Hard iteration limits, "
            "execution timeouts, and human approval gates protect against runaway loops and cost spikes.\n\n"
            "4. Model Context Protocol: MCP standardizes communication between AI clients and external tools using JSON-RPC 2.0."
        )
        embed_service = EmbeddingService()
        doc = RAGDocument(
            filename="ai_engineering_primer.txt",
            file_type="text/plain",
            file_size_bytes=len(starter_text.encode("utf-8")),
            raw_content=starter_text,
            chunk_count=0,
            status="indexed",
        )
        db.session.add(doc)
        db.session.flush()

        chunks = chunk_text(starter_text, chunk_size=300, chunk_overlap=60)
        doc.chunk_count = len(chunks)
        for idx, c_str in enumerate(chunks):
            emb = embed_service.embed(c_str)
            db.session.add(RAGChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=c_str,
                embedding=emb,
                char_count=len(c_str),
            ))

    # 4. Default Application Settings
    if not AppSetting.get("active_provider"):
        AppSetting.set("active_provider", "gemini", "Default LLM provider")
    if not AppSetting.get("theme"):
        AppSetting.set("theme", "dark", "UI theme preference")

    db.session.commit()
    logger.info("Database seeding successfully completed!")
    return True
