"""Abstract base agent and result types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


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
    """Abstract interface for coding agents."""

    def __init__(self, command: str, env: dict[str, str] | None = None, timeout: int = 1800):
        self.command = command
        self.env = env or {}
        self.timeout = timeout

    @abstractmethod
    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        """Run the agent on a task. Returns the generated patch and metadata."""
        ...
