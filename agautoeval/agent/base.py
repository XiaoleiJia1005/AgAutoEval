"""Abstract base agent and result types."""

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

    def __init__(self, command: str, env: dict[str, str] | None = None, timeout: int = 1800):
        self.command = command
        self._env = env or {}
        self._timeout = timeout

    @abstractmethod
    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        """Run the agent on a task. Returns the generated patch and metadata.

        This is used in standalone (non-Docker) mode. In container mode the
        executor calls build_command() instead.
        """
        ...

    @abstractmethod
    def build_command(self, problem_statement: str) -> list[str]:
        """Build the docker exec command to run this agent inside the container.

        Returns a list of strings suitable for passing to Docker exec.
        """
        ...

    def get_install_cmd(self) -> str | None:
        """Shell command to install the agent tool. None if no install needed."""
        return None

    def get_version_cmd(self) -> str | None:
        """Shell command to verify agent installation. None to skip."""
        return None

    def ensure_runtime(self, sandbox: Any) -> None:
        """Ensure runtime dependencies are available in the container.

        Called before get_install_cmd(). Default: no-op.
        """
        pass

    def post_install(self, sandbox: Any) -> None:
        """Post-install steps after running get_install_cmd().

        Called after the install command has been executed. Default: no-op.
        """
        pass

    def get_env(self) -> dict[str, str]:
        """Env vars to pass to docker exec when running the agent."""
        return self._env

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def is_mock(self) -> bool:
        """Whether this agent is a mock (returns ground-truth patch)."""
        return False
