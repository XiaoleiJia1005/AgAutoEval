"""mini-swe-agent message extractor — parses trajectory .traj JSON files."""

import re
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class MiniSWEExtractor(BaseExtractor):
    """Parse mini-swe-agent trajectory files and stdout output."""

    agent_type = "swe_agent"

    _TRAJ_PATTERNS = ["*.traj", "*.traj.json", "trajectory*.json"]
    _STEP_RE = re.compile(
        r"(?:^|\n)(?:─+\s*Step\s+\d+\s*─+|###\s*Step\s+\d+|"
        r"={3,}\s*Step\s+\d+\s*={3,})(.*?)(?=\n(?:─+\s*Step\s+\d+|"
        r"###\s*Step\s+\d+|={3,}\s*Step\s+\d+)|$)",
        re.DOTALL,
    )

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        if persist_dir:
            messages = self._extract_from_trajectories(persist_dir)
            if messages:
                return messages

        content = self._read_file(stdout_path)
        if content:
            return self._extract_from_stdout(content)
        return []

    def _extract_from_trajectories(self, persist_dir: Path) -> list[AgentMessage]:
        newest = self._find_most_recent(persist_dir, self._TRAJ_PATTERNS)
        if not newest:
            return []

        data = self._read_json(newest)
        if not data:
            return []

        messages: list[AgentMessage] = []
        for m in data.get("messages", []):
            role = m.get("role", "unknown")
            content = self._flatten_content(m.get("content", ""))
            if content:
                messages.append(AgentMessage(role=role, content=content))
        return messages

    def _extract_from_stdout(self, stdout: str) -> list[AgentMessage]:
        steps = self._STEP_RE.findall(stdout)
        if steps:
            return [
                AgentMessage(
                    role="assistant",
                    content=step.strip(),
                    metadata={"step": i + 1},
                )
                for i, step in enumerate(steps)
                if step.strip()
            ]

        clean = stdout.strip()
        if clean:
            return [AgentMessage(role="agent", content=clean)]
        return []
