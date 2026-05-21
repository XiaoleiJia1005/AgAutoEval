"""Score computation for evaluation results."""

from typing import Any

from agautoeval.executor import TaskResult


class ScoreReport:
    """Aggregated evaluation metrics."""

    def __init__(self, results: list[TaskResult], metadata: dict[str, Any] | None = None):
        self.total = len(results)
        self.resolved = sum(1 for r in results if r.resolved)
        self.failed = self.total - self.resolved
        self.accuracy = self.resolved / self.total if self.total > 0 else 0.0
        self.total_duration = sum(r.duration for r in results)
        self.avg_duration = self.total_duration / self.total if self.total > 0 else 0.0

        self.errors = [r for r in results if r.error and not r.resolved]
        self.error_count = len(self.errors)

        self.total_f2p = sum(r.f2p_total for r in results)
        self.total_p2p = sum(r.p2p_total for r in results)
        self.f2p_passed = sum(r.f2p_passed for r in results)
        self.p2p_passed = sum(r.p2p_passed for r in results)

        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        d = {
            "total": self.total,
            "resolved": self.resolved,
            "failed": self.failed,
            "accuracy": round(self.accuracy, 4),
            "total_duration": round(self.total_duration, 2),
            "avg_duration": round(self.avg_duration, 2),
            "error_count": self.error_count,
        }
        if self.total_f2p or self.total_p2p:
            d["f2p"] = f"{self.f2p_passed}/{self.total_f2p}"
            d["p2p"] = f"{self.p2p_passed}/{self.total_p2p}"
        if self.metadata:
            d["metadata"] = self.metadata
        return d


def compute_score(
    results: list[TaskResult], metadata: dict[str, Any] | None = None
) -> ScoreReport:
    return ScoreReport(results, metadata=metadata)
