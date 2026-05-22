"""Abstract base agent and result types."""

import shlex
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    patch: str = ""
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    tokens_used: int = 0
    success: bool = True
    error: str = ""


class BaseAgent(ABC):
    """Abstract interface for coding agents.

    The agent is the single source of truth for all agent-specific behavior.
    The executor delegates to agent methods without knowing which agent it is.
    """

    def __init__(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: int = 1800,
        model: str = "",
        provider: str = "",
    ):
        self.command = command
        self._env = env or {}
        self._timeout = timeout
        self.model = model
        self.provider = provider

    # ── template resolution ──────────────────────────────────────

    def _resolve_command(self, problem_statement: str) -> str:
        """Resolve {model}, {provider}, {problem_statement} in a command string.

        {problem_statement} is shell-quoted; {model} and {provider} are
        substituted as-is.
        """
        cmd = self.command
        if "{model}" in cmd:
            cmd = cmd.replace("{model}", self.model or "unknown")
        if "{provider}" in cmd:
            cmd = cmd.replace("{provider}", self.provider or "unknown")
        if "{problem_statement}" in cmd:
            cmd = cmd.replace("{problem_statement}", shlex.quote(problem_statement))
        return cmd

    # ── container mode (primary) ─────────────────────────────────

    def build_command(self, problem_statement: str) -> list[str]:
        """Build the docker exec command.

        Resolves template variables in self.command and wraps in bash -c.
        Override if the agent needs a different execution strategy.
        """
        return ["bash", "-c", self._resolve_command(problem_statement)]

    # ── standalone mode ──────────────────────────────────────────

    @abstractmethod
    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        ...

    # ── install / runtime hooks ──────────────────────────────────

    def get_install_cmd(self) -> str | None:
        return None

    def get_version_cmd(self) -> str | None:
        return None

    def ensure_runtime(self, sandbox: Any) -> None:
        pass

    def post_install(self, sandbox: Any) -> None:
        pass

    # ── env / config ─────────────────────────────────────────────

    def get_env(self) -> dict[str, str]:
        return self._env

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def is_mock(self) -> bool:
        return False
