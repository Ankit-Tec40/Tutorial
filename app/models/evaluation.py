from datetime import datetime
from app.extensions import db


class EvaluationRun(db.Model):
    """Execution history of automated prompt and model evaluations."""
    __tablename__ = "evaluation_runs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    eval_type = db.Column(db.String(50), default="prompt_comparison")  # prompt_comparison, retrieval_quality, model_benchmark
    provider = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    parameters = db.Column(db.JSON, default=dict)
    test_cases = db.Column(db.JSON, default=list)  # list of inputs/expected outputs
    results = db.Column(db.JSON, default=list)     # detailed per-test scores
    metrics = db.Column(db.JSON, default=dict)     # summary metrics {avg_latency_ms, pass_rate, faithfulness, etc.}
    status = db.Column(db.String(30), default="completed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "eval_type": self.eval_type,
            "provider": self.provider,
            "model": self.model,
            "metrics": self.metrics,
            "test_case_count": len(self.test_cases) if self.test_cases else 0,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
