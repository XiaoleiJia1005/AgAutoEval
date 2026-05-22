"""Results reporting - console summary and JSON output."""

import json
from pathlib import Path

from agautoeval.executor import TaskResult
from agautoeval.scorer import ScoreReport


def print_summary(report: ScoreReport, results: list[TaskResult]):
    """Print evaluation summary to console."""
    print()
    print("=" * 70)
    print("                   EVALUATION COMPLETE")
    print("=" * 70)
    print(f"  Total tasks:      {report.total}")
    print(f"  Resolved:         {report.resolved}")
    print(f"  Unresolved:       {report.failed}")
    print(f"  Accuracy:         {report.accuracy:.2%}")
    print(f"  Errors:           {report.error_count}")
    print(f"  Total time:       {report.total_duration:.1f}s")
    print(f"  Avg time/task:    {report.avg_duration:.1f}s")
    print("=" * 70)

    _print_task_table(results)

    if report.errors:
        print()
        print("Errors:")
        for r in report.errors:
            print(f"  [{r.instance_id}] {r.error[:120]}")


def _print_task_table(results: list[TaskResult]):
    has_swebench = any(r.f2p_total or r.p2p_total for r in results)

    if has_swebench:
        print()
        header = f"{'Instance ID':<38} {'Result':<10} {'F2P':>8} {'P2P':>8} {'Time':>8}"
        print(header)
        print("-" * 73)
        for r in results:
            status = "RESOLVED" if r.resolved else ("ERROR" if r.error else "FAIL")
            f2p = f"{r.f2p_passed}/{r.f2p_total}" if r.f2p_total else "-"
            p2p = f"{r.p2p_passed}/{r.p2p_total}" if r.p2p_total else "-"
            print(
                f"{r.instance_id:<38} {status:<10} {f2p:>8} {p2p:>8} {r.duration:>7.1f}s"
            )
    else:
        print()
        print(f"{'Instance ID':<40} {'Result':<10} {'Time':>8}")
        print("-" * 60)
        for r in results:
            status = "PASS" if r.resolved else ("ERROR" if r.error else "FAIL")
            print(f"{r.instance_id:<40} {status:<10} {r.duration:>7.1f}s")


def write_json(
    report: ScoreReport,
    results: list[TaskResult],
    output_path: Path,
):
    """Write full results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "summary": report.to_dict(),
        "results": [r.to_dict() for r in results],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")
