import os
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.rag import RAGDocument, RAGChunk
from app.services.rag.pipeline import RAGPipeline
from app.services.providers.factory import get_providers_status

rag_bp = Blueprint("rag", __name__)
ALLOWED_EXTENSIONS = {"txt", "md", "markdown", "py", "json", "csv"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@rag_bp.route("/rag")
def rag_dashboard():
    """Renders the interactive RAG knowledge base & search lab."""
    documents = RAGDocument.query.order_by(RAGDocument.created_at.desc()).all()
    total_chunks = RAGChunk.query.count()
    provider_status = get_providers_status()

    return render_template(
        "rag.html",
        documents=documents,
        total_chunks=total_chunks,
        provider_status=provider_status,
    )


@rag_bp.route("/api/rag/documents", methods=["GET", "POST"])
def manage_documents():
    """Lists indexed documents or uploads and indexes a new document."""
    if request.method == "GET":
        docs = RAGDocument.query.order_by(RAGDocument.created_at.desc()).all()
        return jsonify([d.to_dict() for d in docs])

    # POST - Document Upload
    pipeline = RAGPipeline()

    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected."}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        clean_name = secure_filename(file.filename)
        try:
            content = file.read().decode("utf-8", errors="replace")
        except Exception as e:
            return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

        doc_type = file.content_type or "text/plain"
    else:
        # JSON text ingestion
        data = request.get_json() or {}
        clean_name = data.get("filename", "notes.txt").strip()
        content = data.get("content", "").strip()
        doc_type = "text/plain"

        if not content:
            return jsonify({"error": "Document content is required."}), 400

    try:
        doc = pipeline.ingest_document(filename=clean_name, content=content, file_type=doc_type)
        return jsonify({
            "success": True,
            "document": doc.to_dict(),
            "message": f"Successfully indexed '{clean_name}' into {doc.chunk_count} chunk(s)."
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rag_bp.route("/api/rag/documents/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id: int):
    """Deletes an indexed document and its vector chunks."""
    doc = RAGDocument.query.get_or_404(doc_id)
    try:
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"success": True, "message": f"Deleted document '{doc.filename}'."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@rag_bp.route("/api/rag/query", methods=["POST"])
def query_rag():
    """Executes a grounded RAG query with source citations."""
    data = request.get_json() or {}
    query_text = data.get("query", "").strip()
    provider_name = data.get("provider")
    model_name = data.get("model")
    top_k = int(data.get("top_k", 4))
    temperature = float(data.get("temperature", 0.2))

    if not query_text:
        return jsonify({"error": "Query cannot be empty."}), 400

    pipeline = RAGPipeline()
    result = pipeline.query_rag(
        query=query_text,
        provider_name=provider_name,
        model_name=model_name,
        top_k=top_k,
        temperature=temperature,
    )
    return jsonify(result)


@rag_bp.route("/api/rag/search", methods=["POST"])
def search_chunks():
    """Retrieval debugging endpoint: returns scored chunks for query inspection."""
    data = request.get_json() or {}
    query_text = data.get("query", "").strip()
    top_k = int(data.get("top_k", 5))

    if not query_text:
        return jsonify({"chunks": []})

    pipeline = RAGPipeline()
    chunks = pipeline.retrieve(query=query_text, top_k=top_k)
    return jsonify({"query": query_text, "chunks": chunks})
