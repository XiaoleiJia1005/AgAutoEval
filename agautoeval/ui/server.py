"""FastAPI server for AgAutoEval results UI.

Start with:  python -m agautoeval.ui.server
             uvicorn agautoeval.ui.server:app --reload
"""

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from agautoeval.ui.extractors import AgentMessage, get_extractor

# Shared canonical list of per-instance log/output files
LOG_FILES = [
    "agent_stdout.log", "agent_stderr.log", "patch.diff",
    "test_output.log", "f2p_failures.log", "p2p_failures.log",
]
ALLOWED_RAW_FILES = set(LOG_FILES + [
    "task_info.json", "result.json", "agent_cmd.json",
])

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

# ── helpers ────────────────────────────────────────────────────────

_BASE_DIR = Path("~/.agautoeval").expanduser().resolve()


def _base_dir() -> Path:
    return _BASE_DIR


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_bytes())
    except (FileNotFoundError, PermissionError, json.JSONDecodeError):
        return None


def _read_yaml(path: Path) -> dict | None:
    try:
        return yaml.safe_load(path.read_bytes())
    except (FileNotFoundError, PermissionError, yaml.YAMLError):
        return None


def _list_runs(base: Path) -> list[dict]:
    if not base.is_dir():
        return []

    runs: list[dict] = []
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue

        run_info: dict[str, Any] = {
            "run_id": d.name,
            "path": str(d),
            "agent_type": "unknown",
            "instance_count": 0,
        }

        data = _read_json(d / "results.json")
        if data:
            s = data.get("summary", {})
            if s:
                run_info.update({
                    "total": s.get("total"),
                    "resolved": s.get("resolved"),
                    "accuracy": s.get("accuracy"),
                    "error_count": s.get("error_count"),
                    "total_duration": s.get("total_duration"),
                })

        cfg = _read_yaml(d / "config.yaml")
        if cfg:
            run_info["agent_type"] = cfg.get("agent", {}).get("type", "unknown")

        run_info["instance_count"] = sum(
            1 for x in d.iterdir() if _is_instance_dir(x)
        )
        runs.append(run_info)

    return runs


def _find_run_dir(base: Path, run_id: str) -> Path:
    run_dir = base / run_id
    if not run_dir.is_dir():
        raise HTTPException(404, f"Run '{run_id}' not found")
    return run_dir


def _is_instance_dir(path: Path) -> bool:
    return path.is_dir() and (path / "results").is_dir()


def _list_instance_dirs(run_dir: Path) -> list[Path]:
    return sorted(
        d for d in run_dir.iterdir() if _is_instance_dir(d)
    )


def _read_instance_info(instance_dir: Path) -> dict[str, Any]:
    results_dir = instance_dir / "results"
    info: dict[str, Any] = {"instance_id": instance_dir.name}

    data = _read_json(results_dir / "task_info.json")
    if data:
        info.update(data)

    data = _read_json(results_dir / "result.json")
    if data:
        info["evaluation"] = data

    logs: dict[str, int] = {}
    for name in LOG_FILES:
        try:
            logs[name] = (results_dir / name).stat().st_size
        except (FileNotFoundError, PermissionError):
            pass
    info["logs"] = logs

    return info


def _read_config_and_extract_agent(run_dir: Path) -> tuple[dict, str]:
    cfg = _read_yaml(run_dir / "config.yaml")
    if cfg:
        return cfg, cfg.get("agent", {}).get("type", "unknown")
    return {}, "unknown"


def _get_persist_dir(run_dir: Path, instance_id: str) -> Path | None:
    mounts_dir = run_dir / instance_id / "mounts"
    return mounts_dir if mounts_dir.is_dir() else None


# ── API Endpoints ──────────────────────────────────────────────────


@app.get("/api/runs")
async def list_runs():
    runs = _list_runs(_base_dir())
    return {"runs": runs, "base_dir": str(_base_dir())}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    config, agent_type = _read_config_and_extract_agent(run_dir)
    summary = _read_json(run_dir / "results.json") or {}

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
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    instance_dir = run_dir / instance_id
    if not instance_dir.is_dir():
        raise HTTPException(404, f"Instance '{instance_id}' not found in run '{run_id}'")

    info = _read_instance_info(instance_dir)
    info["agent_type"] = _read_config_and_extract_agent(run_dir)[1]
    return info


@app.get("/api/runs/{run_id}/instances/{instance_id}/messages")
async def get_instance_messages(run_id: str, instance_id: str):
    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    instance_dir = run_dir / instance_id
    if not instance_dir.is_dir():
        raise HTTPException(404, f"Instance '{instance_id}' not found")

    agent_type = _read_config_and_extract_agent(run_dir)[1]
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
                "metadata": m.metadata,
            }
            for m in messages
        ],
    }


@app.get("/api/runs/{run_id}/instances/{instance_id}/raw/{filename}")
async def get_raw_file(run_id: str, instance_id: str, filename: str):
    if filename not in ALLOWED_RAW_FILES:
        raise HTTPException(403, "Access to this file is not allowed")

    base = _base_dir()
    run_dir = _find_run_dir(base, run_id)

    file_path = run_dir / instance_id / "results" / filename
    try:
        content = file_path.read_text(errors="replace")
    except (FileNotFoundError, PermissionError):
        raise HTTPException(404, f"File '{filename}' not found")

    return PlainTextResponse(content)


# ── CLI ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        prog="agautoeval-ui",
        description="Start the AgAutoEval results UI server",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8520,
        help="Port to bind (default: 8520)",
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    import uvicorn

    base = _base_dir()
    print(f"AgAutoEval UI Server")
    print(f"Data directory: {base}")
    print()

    uvicorn.run(
        "agautoeval.ui.server:app",
        host=args.host,
        port=args.port,
        reload=args.dev,
    )


if __name__ == "__main__":
    main()
