from datetime import datetime
from app.extensions import db


class RAGDocument(db.Model):
    """Uploaded or ingested document for RAG pipelines."""
    __tablename__ = "rag_documents"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    raw_content = db.Column(db.Text, nullable=False)
    chunk_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="indexed")  # 'indexing', 'indexed', 'error'
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Chunks
    chunks = db.relationship(
        "RAGChunk", 
        backref="document", 
        lazy="joined", 
        cascade="all, delete-orphan",
        order_by="RAGChunk.chunk_index"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class RAGChunk(db.Model):
    """An individual text chunk with embedding vector and metadata."""
    __tablename__ = "rag_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=False)  # Float array
    char_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "filename": self.document.filename if self.document else None,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "char_count": self.char_count,
        }
