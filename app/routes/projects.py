import io
import zipfile
from flask import Blueprint, render_template, request, jsonify, send_file, abort
from app.models.project import Project, ProjectFile
from app.services.providers.factory import get_providers_status

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/projects")
def projects_gallery():
    """Renders the Capstone Portfolio Projects catalog."""
    projects = Project.query.order_by(Project.order).all()
    provider_status = get_providers_status()
    return render_template(
        "projects.html",
        projects=projects,
        provider_status=provider_status,
    )


@projects_bp.route("/projects/<slug>")
def project_detail(slug: str):
    """Renders an individual project workbench with file browser and instructions."""
    project = Project.query.filter_by(slug=slug).first_or_404()
    files = project.files
    provider_status = get_providers_status()

    return render_template(
        "project_detail.html",
        project=project,
        files=files,
        provider_status=provider_status,
    )


@projects_bp.route("/api/projects/<slug>/export")
def export_project_zip(slug: str):
    """Generates a downloadable clean ZIP archive of project files."""
    project = Project.query.filter_by(slug=slug).first_or_404()

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add project README
        readme_content = (
            f"# {project.title}\n\n"
            f"**Difficulty:** {project.difficulty} | **Badge:** {project.badge}\n\n"
            f"## Description\n{project.description}\n\n"
            f"## Objectives\n" + "\n".join(f"- {o}" for o in (project.objectives or [])) + "\n\n"
            f"## Requirements\n" + "\n".join(f"- {r}" for r in (project.requirements or [])) + "\n\n"
            f"## Run Instructions\n{project.run_instructions_markdown}\n\n"
            f"## Troubleshooting\n{project.troubleshooting_markdown}\n"
        )
        zf.writestr(f"{project.slug}/README.md", readme_content)

        # Add project files
        for pf in project.files:
            file_entry_path = f"{project.slug}/{pf.filename}"
            zf.writestr(file_entry_path, pf.content)

        # Add clean template .env.example
        env_sample = (
            "# Environment Configuration\n"
            "GEMINI_API_KEY=\n"
            "GEMINI_MODEL=gemini-2.5-flash\n"
            "OLLAMA_BASE_URL=http://localhost:11434\n"
            "OLLAMA_MODEL=llama3.2\n"
        )
        zf.writestr(f"{project.slug}/.env.example", env_sample)

    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{project.slug}.zip",
    )
