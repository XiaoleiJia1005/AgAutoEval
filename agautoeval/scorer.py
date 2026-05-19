"""Score computation for evaluation results."""

from typing import Any

from agautoeval.executor import TaskResult


class ScoreReport:
    """Aggregated evaluation metrics."""

    def __init__(self, results: list[TaskResult]):
        self.total = len(results)
        self.resolved = sum(1 for r in results if r.resolved)
        self.failed = self.total - self.resolved
        self.accuracy = self.resolved / self.total if self.total > 0 else 0.0
        self.total_duration = sum(r.duration for r in results)
        self.avg_duration = self.total_duration / self.total if self.total > 0 else 0.0

        self.errors = [r for r in results if r.error and not r.resolved]
        self.error_count = len(self.errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "resolved": self.resolved,
            "failed": self.failed,
            "accuracy": round(self.accuracy, 4),
            "total_duration": round(self.total_duration, 2),
            "avg_duration": round(self.avg_duration, 2),
            "error_count": self.error_count,
        }


def compute_score(results: list[TaskResult]) -> ScoreReport:
    return ScoreReport(results)
