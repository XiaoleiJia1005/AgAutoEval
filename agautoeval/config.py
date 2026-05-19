"""YAML configuration loading and pydantic validation."""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    type: str = "opencode"
    command: str = "opencode"
    env: dict[str, str] = Field(default_factory=dict)
    timeout: int = 1800


class SandboxConfig(BaseModel):
    image: str = "python:3.10-slim"
    setup_commands: list[str] = Field(default_factory=list)


class DatasetConfig(BaseModel):
    path: str  # local path, HF dataset ID, or URL
    provider: Literal["local", "huggingface", "url"] = "local"
    type: str = "swe_bench"  # dataset format: swe_bench, ...
    split: str = "test"  # HuggingFace split name
    name: str | None = None  # HuggingFace config/subset name
    token: str | None = None  # HF token for private datasets


class ExecutionConfig(BaseModel):
    max_workers: int = 1
    timeout: int = 3600
    retries: int = 0


class OutputConfig(BaseModel):
    dir: str = "results"
    log_level: str = "INFO"


class Config(BaseModel):
    agent: AgentConfig = Field(default_factory=AgentConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    dataset: DatasetConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Config file is empty: {path}")

    return Config.model_validate(raw)
