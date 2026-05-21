"""Agent message extractors — parse agent output into structured messages."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMessage:
    role: str
    content: str
    timestamp: str | None = None
    message_type: str = "text"  # text, tool_call, tool_result, thinking
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseExtractor:
    """Abstract extractor for parsing agent output into messages."""

    agent_type: str = ""

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        """Parse agent output into structured messages."""
        raise NotImplementedError


class FallbackExtractor(BaseExtractor):
    """Returns raw stdout as a single message when no specific extractor exists."""

    agent_type = "fallback"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        if stdout_path.exists():
            content = stdout_path.read_text(errors="replace")
            return [AgentMessage(role="agent", content=content, message_type="text")]
        return []


def get_extractor(agent_type: str) -> BaseExtractor:
    """Factory: return the appropriate extractor for an agent type."""
    registry = {
        "claude": ClaudeCodeExtractor,
        "swe_agent": MiniSWEExtractor,
        "opencode": OpenCodeExtractor,
    }
    cls = registry.get(agent_type, FallbackExtractor)
    return cls()


# Import at bottom to avoid circular imports
from agautoeval.ui.extractors.claude import ClaudeCodeExtractor
from agautoeval.ui.extractors.mini_swe import MiniSWEExtractor
from agautoeval.ui.extractors.opencode import OpenCodeExtractor
