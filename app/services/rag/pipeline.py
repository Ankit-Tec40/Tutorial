import time
import logging
from typing import List, Dict, Any, Optional
from app.extensions import db
from app.models.rag import RAGDocument, RAGChunk
from app.services.embeddings.service import EmbeddingService, cosine_similarity
from app.services.providers.factory import get_provider

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 400, chunk_overlap: int = 80) -> List[str]:
    """Splits a document text into overlapping segments."""
    if not text:
        return []

    # Clean and normalize newlines
    cleaned_text = text.replace("\r\n", "\n").strip()
    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]

    chunks = []
    start = 0
    text_length = len(cleaned_text)

    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunk = cleaned_text[start:text_length].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Attempt to split on paragraph or sentence boundary
        slice_text = cleaned_text[start:end]
        last_para = slice_text.rfind("\n\n")
        last_newline = slice_text.rfind("\n")
        last_period = slice_text.rfind(". ")

        split_at = -1
        if last_para > chunk_size // 2:
            split_at = last_para + 2
        elif last_period > chunk_size // 2:
            split_at = last_period + 2
        elif last_newline > chunk_size // 2:
            split_at = last_newline + 1

        if split_at != -1:
            chunk = cleaned_text[start:start + split_at].strip()
            if chunk:
                chunks.append(chunk)
            start = start + split_at - chunk_overlap
        else:
            chunk = slice_text.strip()
            if chunk:
                chunks.append(chunk)
            start = end - chunk_overlap

        # Ensure forward progress
        if start >= end:
            start = end

    return chunks


class RAGPipeline:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def __init__(self):
        self.embed_service = EmbeddingService()

    def ingest_document(
        self,
        filename: str,
        content: str,
        file_type: str = "text/plain",
        chunk_size: int = 400,
        chunk_overlap: int = 80,
    ) -> RAGDocument:
        """Parses, chunks, embeds, and persists a document."""
        if not content or not content.strip():
            raise ValueError("Document content cannot be empty.")

        doc = RAGDocument(
            filename=filename,
            file_type=file_type,
            file_size_bytes=len(content.encode("utf-8")),
            raw_content=content,
            status="indexing",
        )
        db.session.add(doc)
        db.session.flush()

        try:
            chunks = chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            doc.chunk_count = len(chunks)

            for idx, chunk_str in enumerate(chunks):
                emb = self.embed_service.embed(chunk_str)
                rag_chunk = RAGChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_str,
                    embedding=emb,
                    char_count=len(chunk_str),
                )
                db.session.add(rag_chunk)

            doc.status = "indexed"
            db.session.commit()
            return doc
        except Exception as e:
            db.session.rollback()
            doc.status = "error"
            doc.error_message = str(e)
            db.session.commit()
            logger.error("Failed to ingest document '%s': %s", filename, e)
            raise

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """Retrieves top-k relevant chunks matching query with cosine similarity scores."""
        query_emb = self.embed_service.embed(query)
        all_chunks = RAGChunk.query.all()

        scored_chunks = []
        for ch in all_chunks:
            if not ch.embedding:
                continue
            score = cosine_similarity(query_emb, ch.embedding)
            if score >= score_threshold:
                scored_chunks.append({
                    "id": ch.id,
                    "document_id": ch.document_id,
                    "filename": ch.document.filename if ch.document else "Unknown",
                    "chunk_index": ch.chunk_index,
                    "content": ch.content,
                    "score": round(score, 4),
                })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def query_rag(
        self,
        query: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        top_k: int = 4,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Queries RAG system: retrieves passages, formats context, and grounds generation."""
        start_time = time.perf_counter()
        retrieved_chunks = self.retrieve(query, top_k=top_k)

        # Insufficient evidence check
        if not retrieved_chunks:
            return {
                "query": query,
                "answer": "Insufficient evidence found in the provided documents to answer this question. Please upload relevant reference documents.",
                "sources": [],
                "retrieved_chunks": [],
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                "is_grounded": False,
                "provider": provider_name or "local",
                "model": model_name or "none",
            }

        # Build numbered context passages
        context_blocks = []
        sources = []
        for idx, item in enumerate(retrieved_chunks, start=1):
            source_ref = f"[{idx}] {item['filename']} (chunk {item['chunk_index']}, score: {item['score']})"
            context_blocks.append(f"--- Document Excerpt [{idx}] ({item['filename']}) ---\n{item['content']}")
            sources.append({
                "citation_index": idx,
                "filename": item["filename"],
                "chunk_index": item["chunk_index"],
                "score": item["score"],
                "excerpt": item["content"][:160] + "..." if len(item["content"]) > 160 else item["content"],
            })

        context_text = "\n\n".join(context_blocks)
        system_prompt = (
            "You are a strict, grounded AI assistant answering questions based solely on the provided document excerpts.\n"
            "Rules:\n"
            "1. Only state facts directly supported by the excerpts.\n"
            "2. Cite your sources using bracketed numbers corresponding to the excerpts, e.g. [1], [2].\n"
            "3. If the excerpts do not contain enough information to answer the question, clearly state: "
            "'Insufficient evidence found in the provided documents to fully answer this question.'\n"
            "4. Do not extrapolate or fabricate citations."
        )

        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nGrounded Answer:"

        provider = get_provider(provider_name=provider_name, model_name=model_name)
        try:
            resp = provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "query": query,
                "answer": resp.content,
                "sources": sources,
                "retrieved_chunks": retrieved_chunks,
                "latency_ms": round(elapsed_ms, 2),
                "tokens": {
                    "prompt": resp.prompt_tokens,
                    "completion": resp.completion_tokens,
                    "total": resp.total_tokens,
                },
                "is_grounded": True,
                "provider": resp.provider,
                "model": resp.model,
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("RAG generation error: %s", e)
            return {
                "query": query,
                "answer": f"Error communicating with AI provider ({provider.name}): {str(e)}",
                "sources": sources,
                "retrieved_chunks": retrieved_chunks,
                "latency_ms": round(elapsed_ms, 2),
                "is_grounded": False,
                "error": str(e),
                "provider": provider.name,
                "model": provider.model_name,
            }
