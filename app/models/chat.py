from datetime import datetime
from app.extensions import db


class ChatSession(db.Model):
    """Conversation session in the global AI Workbench."""
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), default="default_user", nullable=False, index=True)
    title = db.Column(db.String(180), default="New Chat")
    provider = db.Column(db.String(40), default="gemini")
    model = db.Column(db.String(80), default="gemini-2.5-flash")
    system_prompt = db.Column(db.Text, default="You are a helpful AI engineering assistant.")
    temperature = db.Column(db.Float, default=0.7)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Messages
    messages = db.relationship(
        "ChatMessage", 
        backref="session", 
        lazy="joined", 
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "provider": self.provider,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ChatMessage(db.Model):
    """Individual message within a chat session."""
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    latency_ms = db.Column(db.Float, nullable=True)
    token_usage = db.Column(db.JSON, nullable=True)
    tool_calls = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "latency_ms": self.latency_ms,
            "token_usage": self.token_usage,
            "tool_calls": self.tool_calls,
            "created_at": self.created_at.isoformat(),
        }
