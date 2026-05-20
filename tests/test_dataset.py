"""Unit tests for dataset loading and F2P/P2P field normalization."""

import json
import tempfile
from pathlib import Path

from agautoeval.dataset import Task, _parse_items


def _write_json(data, dir="") -> Path:
    p = Path(dir) / "test_dataset.json"
    p.write_text(json.dumps(data))
    return p


# ── Task model validation ──────────────────────────────────────────


def test_task_accepts_lowercase_f2p_p2p():
    t = Task.model_validate({
        "instance_id": "a",
        "repo": "r",
        "base_commit": "b",
        "problem_statement": "ps",
        "fail_to_pass": ["test_a", "test_b"],
        "pass_to_pass": ["test_c"],
    })
    assert t.fail_to_pass == ["test_a", "test_b"]
    assert t.pass_to_pass == ["test_c"]


def test_task_ignores_uppercase_f2p_p2p_by_default():
    """Without normalization, pydantic silently drops uppercase keys."""
    t = Task.model_validate({
        "instance_id": "a",
        "repo": "r",
        "base_commit": "b",
        "problem_statement": "ps",
        "FAIL_TO_PASS": ["test_a"],
        "PASS_TO_PASS": ["test_c"],
    })
    assert t.fail_to_pass == []
    assert t.pass_to_pass == []


def test_task_f2p_p2p_defaults():
    t = Task.model_validate({
        "instance_id": "a",
        "repo": "r",
        "base_commit": "b",
        "problem_statement": "ps",
    })
    assert t.fail_to_pass == []
    assert t.pass_to_pass == []


# ── _parse_items ───────────────────────────────────────────────────


def test_parse_items_from_list_with_lowercase():
    items = [
        {"instance_id": "a", "repo": "r", "base_commit": "b", "problem_statement": "ps",
         "fail_to_pass": ["t1"], "pass_to_pass": ["t2"]},
        {"instance_id": "b", "repo": "r2", "base_commit": "b2", "problem_statement": "ps2",
         "fail_to_pass": [], "pass_to_pass": ["t3"]},
    ]
    tasks = _parse_items(items)
    assert len(tasks) == 2
    assert tasks[0].instance_id == "a"
    assert tasks[0].fail_to_pass == ["t1"]
    assert tasks[0].pass_to_pass == ["t2"]
    assert tasks[1].fail_to_pass == []
    assert tasks[1].pass_to_pass == ["t3"]


def test_parse_items_from_dict():
    items = {
        "a": {"instance_id": "a", "repo": "r", "base_commit": "b", "problem_statement": "ps",
              "fail_to_pass": ["t1"], "pass_to_pass": []},
    }
    tasks = _parse_items(items)
    assert len(tasks) == 1
    assert tasks[0].instance_id == "a"
    assert tasks[0].fail_to_pass == ["t1"]


def test_parse_items_maintains_f2p_p2p_counts():
    items = [
        {"instance_id": "i1", "repo": "r1", "base_commit": "b1", "problem_statement": "ps1",
         "fail_to_pass": ["t1", "t2", "t3"], "pass_to_pass": ["t4"]},
        {"instance_id": "i2", "repo": "r2", "base_commit": "b2", "problem_statement": "ps2",
         "fail_to_pass": [], "pass_to_pass": ["t5", "t6"]},
    ]
    tasks = _parse_items(items)
    assert len(tasks[0].fail_to_pass) == 3
    assert len(tasks[0].pass_to_pass) == 1
    assert len(tasks[1].fail_to_pass) == 0
    assert len(tasks[1].pass_to_pass) == 2


# ── Local JSON loading (round-trip) ────────────────────────────────


def test_local_load_f2p_p2p():
    from agautoeval.dataset import _load_local
    data = {
        "i1": {
            "instance_id": "i1", "repo": "r1", "base_commit": "b1",
            "problem_statement": "ps1", "fail_to_pass": ["t1", "t2"],
            "pass_to_pass": ["t3"],
        },
    }
    with tempfile.TemporaryDirectory() as td:
        p = _write_json(data, dir=td)
        result = _load_local(str(p))
    assert "i1" in result
    assert result["i1"]["fail_to_pass"] == ["t1", "t2"]
    assert result["i1"]["pass_to_pass"] == ["t3"]


def test_local_load_empty_f2p_p2p():
    from agautoeval.dataset import _load_local
    data = {
        "i1": {
            "instance_id": "i1", "repo": "r1", "base_commit": "b1",
            "problem_statement": "ps1", "fail_to_pass": [], "pass_to_pass": [],
        },
    }
    with tempfile.TemporaryDirectory() as td:
        p = _write_json(data, dir=td)
        result = _load_local(str(p))
    assert result["i1"]["fail_to_pass"] == []
    assert result["i1"]["pass_to_pass"] == []


# ── End-to-end: load_dataset → F2P/P2P counts ──────────────────────


def test_load_dataset_counts_f2p_p2p():
    from agautoeval.dataset import load_dataset
    from agautoeval.config import DatasetConfig
    data = {
        "a": {"instance_id": "a", "repo": "r", "base_commit": "b", "problem_statement": "ps",
              "fail_to_pass": ["t1", "t2"], "pass_to_pass": ["t3", "t4"]},
        "b": {"instance_id": "b", "repo": "r2", "base_commit": "b2", "problem_statement": "ps2",
              "fail_to_pass": ["t5"], "pass_to_pass": []},
    }
    with tempfile.TemporaryDirectory() as td:
        p = _write_json(data, dir=td)
        cfg = DatasetConfig(provider="local", path=str(p))
        tasks = load_dataset(cfg)

    assert len(tasks) == 2
    total_f2p = sum(len(t.fail_to_pass) for t in tasks)
    total_p2p = sum(len(t.pass_to_pass) for t in tasks)
    assert total_f2p == 3
    assert total_p2p == 2
    assert tasks[0].fail_to_pass == ["t1", "t2"]
    assert tasks[0].pass_to_pass == ["t3", "t4"]
    assert tasks[1].fail_to_pass == ["t5"]
    assert tasks[1].pass_to_pass == []
