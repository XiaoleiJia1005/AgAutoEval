#!/usr/bin/env python3
"""Generate fake evaluation results for UI testing.

Usage: python scripts/generate_fake_data.py
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path("~/.agautoeval").expanduser().resolve()
BASE.mkdir(parents=True, exist_ok=True)

SCENARIOS = [
    {"agent_type": "swe_agent", "model": "deepseek-v4-pro",   "provider": "deepseek",  "accuracy": 0.52},
    {"agent_type": "swe_agent", "model": "deepseek-v3",      "provider": "deepseek",  "accuracy": 0.45},
    {"agent_type": "opencode",  "model": "deepseek-v4-pro",   "provider": "deepseek",  "accuracy": 0.48},
    {"agent_type": "claude",    "model": "claude-sonnet-4-6", "provider": "anthropic", "accuracy": 0.61},
    {"agent_type": "claude",    "model": "claude-opus-4-7",   "provider": "anthropic", "accuracy": 0.68},
    {"agent_type": "swe_agent", "model": "gpt-4.1",          "provider": "openai",    "accuracy": 0.44},
    {"agent_type": "opencode",  "model": "claude-sonnet-4-6", "provider": "anthropic", "accuracy": 0.55},
]

INSTANCES = [
    {"id": "sympy__sympy-12481",              "repo": "sympy/sympy",               "f2p": 3, "p2p": 2},
    {"id": "django__django-12345",             "repo": "django/django",             "f2p": 5, "p2p": 3},
    {"id": "scikit-learn__scikit-learn-13241", "repo": "scikit-learn/scikit-learn", "f2p": 2, "p2p": 4},
    {"id": "matplotlib__matplotlib-23456",     "repo": "matplotlib/matplotlib",     "f2p": 4, "p2p": 2},
    {"id": "astropy__astropy-12907",           "repo": "astropy/astropy",           "f2p": 3, "p2p": 3},
    {"id": "pytest-dev__pytest-5678",          "repo": "pytest-dev/pytest",         "f2p": 6, "p2p": 4},
    {"id": "pandas-dev__pandas-34567",         "repo": "pandas-dev/pandas",         "f2p": 4, "p2p": 5},
    {"id": "sphinx-doc__sphinx-89012",         "repo": "sphinx-doc/sphinx",         "f2p": 2, "p2p": 1},
    {"id": "psf__requests-45678",              "repo": "psf/requests",              "f2p": 3, "p2p": 2},
    {"id": "pallets__flask-90123",             "repo": "pallets/flask",             "f2p": 5, "p2p": 3},
]


def make_stdout(agent_type: str, inst_id: str, resolved: bool) -> str:
    short = inst_id.split("__")[1]
    if agent_type == "claude":
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": f"Fix the bug in {inst_id}"}, "timestamp": "2026-05-20T10:00:00Z"}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "I'll analyze this issue step by step."}]}, "timestamp": "2026-05-20T10:00:05Z"}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "grep -r 'bug' src/"}}]}, "timestamp": "2026-05-20T10:00:10Z"}),
            json.dumps({"type": "user", "message": {"role": "user", "content": "Tool output:\ncore.py:42: return data / 0  # bug here"}}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Found the division by zero. Let me fix it."}]}, "timestamp": "2026-05-20T10:00:15Z"}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": "core.py", "content": "..."}}]}, "timestamp": "2026-05-20T10:00:20Z"}),
        ]
        if resolved:
            lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Fix complete. All tests pass."}]}, "timestamp": "2026-05-20T10:00:30Z"}))
        return "\n".join(lines)

    elif agent_type == "opencode":
        content = (
            "Thinking:\nI need to understand the codebase and locate the bug.\n\n"
            "Action:\nbash grep -n 'bug' src/\n\n"
            f"Observation:\n{short}/core.py:42: return data / 0  # bug\n\n"
            f"Action:\nbash sed -i 's/bug/fix/' {short}/core.py\n\n"
            "Observation:\nFile modified\n\n"
            "Action:\nbash pytest tests/ -x -q\n\n"
        )
        content += ("Observation:\nAll tests passed!\n\nResponse: Fix applied and verified.\n"
                    if resolved else
                    "Observation:\n1 test failed\n\nThinking: Need more work on edge cases.\n")
        return content

    else:  # swe_agent / mini-swe-agent
        steps = (
            "── Step 1 ──\n"
            "Model thinking: I need to understand the issue.\n"
            "Action: bash cat core.py\n\n"
            "── Step 2 ──\n"
            f"Found the bug in {short}/core.py\n"
            "Action: bash sed -i 's/bug/fix/' core.py\n"
            "Observation: File modified successfully\n\n"
            "── Step 3 ──\n"
            "Running tests to verify...\n"
            "Action: bash pytest tests/test_core.py -x\n"
        )
        if resolved:
            steps += "Observation: 3 passed in 2.34s\n\nAll tests passed! Submitting patch.\n"
        else:
            steps += "Observation: 1 failed, 2 passed\n\nTests not fully passing.\n"
        return steps


def main():
    base_time = datetime(2026, 5, 20, 10, 0, 0)

    for i, sc in enumerate(SCENARIOS):
        run_time = base_time + timedelta(hours=i * 6)
        run_id = run_time.strftime("%Y%m%d_%H%M%S")
        run_dir = BASE / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        total_inst = random.randint(5, 10)
        selected = random.sample(INSTANCES, min(total_inst, len(INSTANCES)))
        target_resolved = max(1, int(len(selected) * sc["accuracy"]))

        resolved_mask = [True] * target_resolved + [False] * (len(selected) - target_resolved)
        random.shuffle(resolved_mask)

        total_duration = 0.0
        results_list = []
        for j, inst in enumerate(selected):
            resolved = resolved_mask[j]
            dur = random.uniform(300, 1400)
            total_duration += dur
            agent_dur = dur * random.uniform(0.75, 0.95)
            f2p_passed = inst["f2p"] if resolved else random.randint(0, inst["f2p"] - 1)
            p2p_passed = inst["p2p"] if resolved else max(0, inst["p2p"] - random.randint(1, inst["p2p"]))

            results_list.append({
                "instance_id": inst["id"],
                "resolved": resolved,
                "duration": round(dur, 1),
                "f2p": f"{f2p_passed}/{inst['f2p']}",
                "p2p": f"{p2p_passed}/{inst['p2p']}",
            })

            # Per-instance files
            inst_dir = run_dir / inst["id"] / "results"
            inst_dir.mkdir(parents=True, exist_ok=True)

            (inst_dir / "task_info.json").write_text(json.dumps({
                "instance_id": inst["id"],
                "repo": inst["repo"],
                "base_commit": f"{random.getrandbits(40):040x}"[:8],
                "agent_type": sc["agent_type"],
                "f2p_count": inst["f2p"],
                "p2p_count": inst["p2p"],
                "problem_statement": f"Fix the bug in {inst['repo'].split('/')[1]} where edge case causes incorrect results.",
            }, indent=2))

            (inst_dir / "result.json").write_text(json.dumps({
                "instance_id": inst["id"],
                "resolved": resolved,
                "error": "" if resolved else "Test failure in edge case",
                "duration": round(dur, 1),
                "agent_duration": round(agent_dur, 1),
                "f2p": f"{f2p_passed}/{inst['f2p']}",
                "p2p": f"{p2p_passed}/{inst['p2p']}",
                "timing": {"prepare": round(random.uniform(10, 30), 1), "agent": round(agent_dur, 1), "evaluate": round(random.uniform(5, 20), 1)},
            }, indent=2))

            (inst_dir / "agent_stdout.log").write_text(make_stdout(sc["agent_type"], inst["id"], resolved))

            (inst_dir / "patch.diff").write_text(
                "diff --git a/core.py b/core.py\n"
                f"index {random.getrandbits(32):08x}..{random.getrandbits(32):08x} 100644\n"
                "--- a/core.py\n+++ b/core.py\n"
                "@@ -100,6 +100,8 @@\n def process(data):\n"
                "+    if data is None: return []\n"
                "     return [x for x in data if x > 0]\n"
            )

            f2p_lines = [f"tests/test_core.py::test_edge_cases PASSED [  {k*20:3}%]" for k in range(1, 6)]
            if not resolved:
                f2p_lines.append("tests/test_core.py::test_boundary FAILED [ 100%]")
            (inst_dir / "test_output.log").write_text("\n".join(f2p_lines))

        (run_dir / "config.yaml").write_text(
            f"agent:\n  type: {sc['agent_type']}\n  model: {sc['model']}\n  provider: {sc['provider']}\n  timeout: 1800\n")

        (run_dir / "results.json").write_text(json.dumps({
            "summary": {
                "total": len(selected),
                "resolved": target_resolved,
                "failed": len(selected) - target_resolved,
                "accuracy": round(target_resolved / len(selected), 4),
                "total_duration": round(total_duration, 1),
                "avg_duration": round(total_duration / len(selected), 1),
                "error_count": 0,
                "metadata": {
                    "agent_type": sc["agent_type"], "model": sc["model"],
                    "provider": sc["provider"], "dataset_path": "SWE-bench/SWE-bench_Verified",
                    "dataset_provider": "huggingface", "dataset_type": "swe_bench",
                    "run_id": run_id,
                },
            },
            "results": results_list,
        }, indent=2, ensure_ascii=False))

        print(f"  {run_id}  {sc['agent_type']:10s} {sc['provider']:10s} {sc['model']:22s}  accuracy={sc['accuracy']:.0%}  instances={len(selected)}")

    print(f"\nDone — {len(SCENARIOS)} runs in {BASE}")


if __name__ == "__main__":
    main()
