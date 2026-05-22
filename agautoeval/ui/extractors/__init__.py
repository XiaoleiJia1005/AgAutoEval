"""Agent message extractors — parse agent output into structured messages."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMessage:
    role: str
    content: str
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseExtractor:
    """Abstract extractor for parsing agent output into messages."""

    agent_type: str = ""

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        raise NotImplementedError

    @staticmethod
    def _flatten_content(content: str | list) -> str:
        """Flatten OpenAI-style content from list-of-dicts to a single string."""
        if isinstance(content, list):
            return " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c)
                for c in content
            )
        return str(content) if content else ""

    @staticmethod
    def _find_most_recent(base_dir: Path, patterns: list[str]) -> Path | None:
        """Find the most recently modified file matching any glob pattern."""
        newest: Path | None = None
        newest_mtime = 0
        for pattern in patterns:
            for f in base_dir.rglob(pattern):
                mtime = f.stat().st_mtime
                if mtime > newest_mtime:
                    newest = f
                    newest_mtime = mtime
        return newest

    @staticmethod
    def _read_file(path: Path) -> str | None:
        """Read a file, returning None rather than raising if it doesn't exist."""
        try:
            return path.read_text(errors="replace")
        except (FileNotFoundError, PermissionError):
            return None

    @staticmethod
    def _read_json(path: Path) -> dict | None:
        import json
        try:
            return json.loads(path.read_bytes())
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            return None


class FallbackExtractor(BaseExtractor):
    """Returns raw stdout as a single message when no specific extractor exists."""

    agent_type = "fallback"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        content = self._read_file(stdout_path)
        if content:
            return [AgentMessage(role="agent", content=content)]
        return []


def get_extractor(agent_type: str) -> BaseExtractor:
    registry = {
        "claude": ClaudeCodeExtractor,
        "swe_agent": MiniSWEExtractor,
        "opencode": OpenCodeExtractor,
    }
    cls = registry.get(agent_type, FallbackExtractor)
    return cls()


from agautoeval.ui.extractors.claude import ClaudeCodeExtractor
from agautoeval.ui.extractors.mini_swe import MiniSWEExtractor
from agautoeval.ui.extractors.opencode import OpenCodeExtractor
