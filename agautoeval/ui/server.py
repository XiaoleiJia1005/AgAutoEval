"""FastAPI server for AgAutoEval results UI.

Start with:  python -m agautoeval.ui.server
             uvicorn agautoeval.ui.server:app --reload
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from agautoeval.ui.extractors import AgentMessage, get_extractor

app = FastAPI(
    title="AgAutoEval UI",
    description="Browse evaluation runs, instances, and agent messages",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _base_dir() -> Path:
    """Resolve the base output directory from config or default."""
    return Path("~/.agautoeval").expanduser().resolve()


def _list_runs(base: Path) -> list[dict]:
    """List all run directories with metadata."""
    runs: list[dict] = []
    if not base.is_dir():
        return runs

    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        run_info: dict[str, Any] = {
            "run_id": d.name,
            "path": str(d),
        }

        # Try to read results.json for summary
        results_file = d / "results.json"
        if results_file.exists():
            try:
                data = json.loads(results_file.read_text())
                summary = data.get("summary", {})
                run_info["total"] = summary.get("total", 0)
                run_info["resolved"] = summary.get("resolved", 0)
                run_info["accuracy"] = summary.get("accuracy", 0)
                run_info["error_count"] = summary.get("error_count", 0)
                run_info["total_duration"] = summary.get("total_duration", 0)
            except (json.JSONDecodeError, KeyError):
                pass

        # Try to read config for agent type
        config_file = d / "config.yaml"
        if config_file.exists():
            try:
                cfg = yaml.safe_load(config_file.read_text())
                run_info["agent_type"] = cfg.get("agent", {}).get("type", "unknown")
            except (yaml.YAMLError, AttributeError):
                run_info["agent_type"] = "unknown"
        else:
            run_info["agent_type"] = "unknown"

        # Try to list instances
        instances = _list_instance_dirs(d)
        run_info["instance_count"] = len(instances)

        runs.append(run_info)

    return runs


def _find_run_dir(base: Path, run_id: str) -> Path:
    """Find and validate a run directory."""
    run_dir = base / run_id
    if not run_dir.is_dir():
        raise HTTPException(404, f"Run '{run_id}' not found")
    return run_dir


def _is_instance_dir(path: Path) -> bool:
    """Check if a path is an instance directory (has a results/ subdir)."""
    return path.is_dir() and (path / "results").is_dir()


def _list_instance_dirs(run_dir: Path) -> list[Path]:
    """List all instance directories in a run."""
    instances: list[Path] = []
    for d in run_dir.iterdir():
        if _is_instance_dir(d):
            instances.append(d)
    return sorted(instances)


def _read_instance_info(instance_dir: Path) -> dict[str, Any]:
    """Read task_info.json for an instance."""
    results_dir = instance_dir / "results"
    info = {"instance_id": instance_dir.name}

    task_info = results_dir / "task_info.json"
    if task_info.exists():
        try:
            info.update(json.loads(task_info.read_text()))
        except (json.JSONDecodeError, KeyError):
            pass

    result_file = results_dir / "result.json"
    if result_file.exists():
        try:
            info["evaluation"] = json.loads(result_file.read_text())
        except (json.JSONDecodeError, KeyError):
            pass

    # Check what log files exist
    logs: dict[str, int] = {}
    for log_name in [
        "agent_stdout.log", "agent_stderr.log", "patch.diff",
        "test_output.log", "f2p_failures.log", "p2p_failures.log",
    ]:
        log_path = results_dir / log_name
        if log_path.exists():
            logs[log_name] = log_path.stat().st_size
    info["logs"] = logs

    return info


def _get_agent_type(run_dir: Path) -> str:
    """Determine the agent type from the config saved in the run dir."""
    config_file = run_dir / "config.yaml"
    if config_file.exists():
        try:
            cfg = yaml.safe_load(config_file.read_text())
            return cfg.get("agent", {}).get("type", "unknown")
        except (yaml.YAMLError, AttributeError):
            pass
    return "unknown"


def _get_persist_dir(run_dir: Path, instance_id: str) -> Path | None:
    """Get the persist (mounts) directory for an instance."""
    mounts_dir = run_dir / instance_id / "mounts"
    if mounts_dir.is_dir():
        return mounts_dir
    return None


# ── API Endpoints ──────────────────────────────────────────────────


@app.get("/api/runs")
async def list_runs():
    """List all evaluation runs."""
    runs = _list_runs(_base_dir())
    return {"runs": runs, "base_dir": str(_base_dir())}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """Get details for a specific run, including all instances."""
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    agent_type = _get_agent_type(run_dir)

    # Read results summary
    summary = {}
    results_file = run_dir / "results.json"
    if results_file.exists():
        try:
            summary = json.loads(results_file.read_text())
        except (json.JSONDecodeError, KeyError):
            pass

    # Read config
    config = {}
    config_file = run_dir / "config.yaml"
    if config_file.exists():
        try:
            config = yaml.safe_load(config_file.read_text())
        except (yaml.YAMLError, AttributeError):
            pass

    # List instances
    instance_dirs = _list_instance_dirs(run_dir)
    instances = [_read_instance_info(d) for d in instance_dirs]

    return {
        "run_id": run_id,
        "agent_type": agent_type,
        "config": config,
        "summary": summary,
        "instances": instances,
    }


@app.get("/api/runs/{run_id}/instances/{instance_id}")
async def get_instance(run_id: str, instance_id: str):
    """Get details for a specific instance."""
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    instance_dir = run_dir / instance_id
    if not instance_dir.is_dir():
        raise HTTPException(404, f"Instance '{instance_id}' not found in run '{run_id}'")

    info = _read_instance_info(instance_dir)
    agent_type = _get_agent_type(run_dir)
    info["agent_type"] = agent_type

    return info


@app.get("/api/runs/{run_id}/instances/{instance_id}/messages")
async def get_instance_messages(run_id: str, instance_id: str):
    """Get parsed agent messages for an instance."""
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    instance_dir = run_dir / instance_id
    if not instance_dir.is_dir():
        raise HTTPException(404, f"Instance '{instance_id}' not found")

    agent_type = _get_agent_type(run_dir)
    extractor = get_extractor(agent_type)

    stdout_path = instance_dir / "results" / "agent_stdout.log"
    persist_dir = _get_persist_dir(run_dir, instance_id)

    messages: list[AgentMessage] = extractor.extract(stdout_path, persist_dir)

    return {
        "instance_id": instance_id,
        "agent_type": agent_type,
        "message_count": len(messages),
        "has_stdout": stdout_path.exists(),
        "has_persist": persist_dir is not None,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "message_type": m.message_type,
                "metadata": m.metadata,
            }
            for m in messages
        ],
    }


@app.get("/api/runs/{run_id}/instances/{instance_id}/raw/{filename}")
async def get_raw_file(run_id: str, instance_id: str, filename: str):
    """Get a raw log file for an instance (agent_stdout.log, patch.diff, etc.)."""
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    file_path = run_dir / instance_id / "results" / filename
    if not file_path.exists():
        raise HTTPException(404, f"File '{filename}' not found")

    # Only allow known log files
    allowed = {
        "agent_stdout.log", "agent_stderr.log", "patch.diff",
        "test_output.log", "f2p_failures.log", "p2p_failures.log",
        "task_info.json", "result.json", "agent_cmd.json",
    }
    if filename not in allowed:
        raise HTTPException(403, "Access to this file is not allowed")

    content = file_path.read_text(errors="replace")
    return PlainTextResponse(content)


def main():
    """CLI entry point: python -m agautoeval.ui.server"""
    import uvicorn

    base = _base_dir()
    print(f"AgAutoEval UI Server")
    print(f"Data directory: {base}")
    print(f"Runs found: {len(_list_runs(base))}")
    print()

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8520

    uvicorn.run("agautoeval.ui.server:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
