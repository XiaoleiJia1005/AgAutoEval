"""Dataset loader with multi-provider support.

Supported providers:
  - local:       JSON file on local filesystem
  - huggingface: Dataset from HuggingFace Hub
  - url:         JSON fetched from a URL
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agautoeval.config import DatasetConfig


class Task(BaseModel):
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: str = ""
    test_patch: str = ""
    version: str = ""
    fail_to_pass: list[str] = []
    pass_to_pass: list[str] = []


def load_dataset(cfg: DatasetConfig) -> list[Task]:
    """Load tasks from the configured provider."""
    if cfg.provider == "local":
        data = _load_local(cfg.path)
    elif cfg.provider == "huggingface":
        data = _load_huggingface(cfg.path, cfg.split, cfg.name, cfg.token)
    elif cfg.provider == "url":
        data = _load_url(cfg.path)
    else:
        raise ValueError(f"Unknown provider: {cfg.provider}")

    return _parse_items(data)


def slice_dataset(tasks: list[Task], start: int = 0, end: int | None = None) -> list[Task]:
    """Slice dataset for partial evaluation runs."""
    return tasks[start:end]


# ── internal helpers ────────────────────────────────────────────

def _parse_items(data: Any) -> list[Task]:
    """Normalize raw JSON data into a list of Task objects."""
    if isinstance(data, dict):
        items = list(data.values())
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"Unexpected dataset format: {type(data)}")
    return [Task.model_validate(item) for item in items]


def _load_local(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset file not found: {p}")
    with open(p) as f:
        return json.load(f)


def _load_huggingface(
    dataset_id: str,
    split: str = "test",
    name: str | None = None,
    token: str | None = None,
) -> Any:
    """Load dataset from HuggingFace Hub.

    Tries the ``datasets`` library first, falling back to the Hub API.
    """
    try:
        from datasets import load_dataset as hf_load
    except ImportError:
        return _load_huggingface_via_api(dataset_id, split, name, token)

    kwargs: dict[str, Any] = {"split": split}
    if name:
        kwargs["name"] = name
    if token:
        kwargs["token"] = token

    ds = hf_load(dataset_id, **kwargs)
    rows = ds.to_list()

    # HF stores F2P/P2P as JSON strings — parse them
    for row in rows:
        for field in ("fail_to_pass", "FAIL_TO_PASS"):
            if field in row and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        for field in ("pass_to_pass", "PASS_TO_PASS"):
            if field in row and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    pass

    return rows


def _load_huggingface_via_api(
    dataset_id: str,
    split: str = "test",
    name: str | None = None,
    token: str | None = None,
) -> Any:
    """Fallback: load via HuggingFace datasets-server API.

    Handles pagination (API returns max 100 rows per request) and parses
    JSON-encoded F2P/P2P fields.
    """
    import urllib.request
    import urllib.error

    config_part = name or "default"
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    all_rows: list[dict] = []
    offset = 0
    page_size = 100

    while True:
        url = (
            f"https://datasets-server.huggingface.co/rows"
            f"?dataset={dataset_id}&config={config_part}&split={split}"
            f"&offset={offset}&length={page_size}"
        )
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Failed to load HuggingFace dataset '{dataset_id}': {e}"
            ) from e

        page_rows = body.get("rows", [])
        if not page_rows:
            break
        all_rows.extend(r["row"] for r in page_rows)

        if len(page_rows) < page_size:
            break
        offset += page_size

    # Parse JSON-encoded F2P/P2P fields (same as _load_huggingface)
    for row in all_rows:
        for field in ("fail_to_pass", "FAIL_TO_PASS"):
            if field in row and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        for field in ("pass_to_pass", "PASS_TO_PASS"):
            if field in row and isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    pass

    return all_rows


def _load_url(url: str) -> Any:
    """Load dataset JSON from a URL."""
    import urllib.request
    import urllib.error

    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to load dataset from URL '{url}': {e}") from e
