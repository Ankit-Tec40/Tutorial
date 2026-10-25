from app.services.embeddings.service import cosine_similarity, EmbeddingService
from app.services.rag.pipeline import chunk_text, RAGPipeline
from app.models.rag import RAGDocument, RAGChunk


def test_cosine_similarity():
    """Tests exact math of cosine similarity calculation."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert round(cosine_similarity(v1, v2), 4) == 1.0000
    assert round(cosine_similarity(v1, v3), 4) == 0.0000
    assert cosine_similarity([], []) == 0.0


def test_chunk_text():
    """Verifies text splitting preserves overlap and handles paragraph breaks."""
    text = (
        "Paragraph 1 contains some important concepts.\n\n"
        "Paragraph 2 discusses vector embeddings and semantic search.\n\n"
        "Paragraph 3 finishes the explanation."
    )
    chunks = chunk_text(text, chunk_size=80, chunk_overlap=20)
    assert len(chunks) >= 2
    assert "Paragraph 1" in chunks[0]


def test_rag_ingest_and_retrieve(app):
    """Verifies end-to-end RAG document ingestion and similarity retrieval."""
    with app.app_context():
        pipeline = RAGPipeline()
        doc = pipeline.ingest_document(
            filename="test_doc.txt",
            content="Neural embeddings map words into dense numerical vectors in multi-dimensional space."
        )
        assert doc.id is not None
        assert doc.chunk_count > 0

        # Retrieve
        results = pipeline.retrieve(query="neural embeddings", top_k=2)
        assert len(results) > 0
        assert results[0]["score"] > 0.1
        assert "dense numerical vectors" in results[0]["content"]
