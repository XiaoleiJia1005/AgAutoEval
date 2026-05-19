"""YAML configuration loading and pydantic validation."""

import re
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
    mode: Literal["auto", "prebuilt"] = "auto"
    repo_path: str = "/repo"  # path inside container where repo lives
    setup_commands: list[str] = Field(default_factory=list)
    cleanup_image: bool = False  # docker rmi after each task to save disk

    # ── template resolution ─────────────────────────────────────

    def resolve_image(self, task_fields: dict[str, Any]) -> str:
        """Resolve template variables in the image string.

        Supports:
          {field}              — direct field value
          {field|split:d:i}    — split field by delim, take index i

        Example:
          image: "sweb.eval.{instance_id|split:__:0}_1776_{instance_id|split:__:1}"
          with instance_id="sympy__sympy-12481"
          → "sweb.eval.sympy_1776_sympy-12481"
        """
        return self._resolve(self.image, task_fields)

    def resolve_setup_commands(self, task_fields: dict[str, Any]) -> list[str]:
        """Resolve template variables in each setup command."""
        return [self._resolve(cmd, task_fields) for cmd in self.setup_commands]

    @staticmethod
    def _resolve(template: str, fields: dict[str, Any]) -> str:
        def _replacer(m: re.Match) -> str:
            expr = m.group(1)
            if "|" in expr:
                var, *transforms = expr.split("|")
                val = str(fields.get(var, m.group(0)))
                for tf in transforms:
                    val = SandboxConfig._apply_transform(val, tf)
                return val
            return str(fields.get(expr, m.group(0)))

        return re.sub(r"\{([^}]+)\}", _replacer, template)

    @staticmethod
    def _apply_transform(value: str, transform: str) -> str:
        parts = transform.split(":")
        name = parts[0]
        args = parts[1:]

        if name == "split":
            delim = args[0] if args else ","
            idx = int(args[1]) if len(args) > 1 else 0
            return value.split(delim)[idx]

        return value


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
