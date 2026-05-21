"""mini-swe-agent message extractor — parses trajectory .traj JSON files."""

import json
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class MiniSWEExtractor(BaseExtractor):
    """Parse mini-swe-agent output.

    mini-swe-agent stores structured messages in trajectory .traj.json files
    under trajectories/ in the working directory. We parse these first,
    then fall back to parsing raw stdout for any agent-like output.
    """

    agent_type = "swe_agent"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        messages: list[AgentMessage] = []

        # 1. Try trajectory files from persist
        if persist_dir:
            messages = self._extract_from_trajectories(persist_dir)

        # 2. Fall back to parsing stdout
        if not messages and stdout_path.exists():
            messages = self._extract_from_stdout(stdout_path.read_text(errors="replace"))

        return messages

    def _extract_from_trajectories(self, persist_dir: Path) -> list[AgentMessage]:
        messages: list[AgentMessage] = []

        # Look for traj files in persist_dir
        traj_files: list[Path] = []
        for f in persist_dir.rglob("*.traj"):
            traj_files.append(f)
        for f in persist_dir.rglob("*.traj.json"):
            traj_files.append(f)
        for f in persist_dir.rglob("trajectory*.json"):
            traj_files.append(f)

        if not traj_files:
            return messages

        # Sort by modification time, use most recent
        traj_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for traj_file in traj_files[:1]:  # Just the most recent
            try:
                data = json.loads(traj_file.read_text())
                msgs = data.get("messages", [])
                for m in msgs:
                    role = m.get("role", "unknown")
                    content = m.get("content", "")
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") if isinstance(c, dict) else str(c)
                            for c in content
                        )
                    if content:
                        messages.append(AgentMessage(
                            role=role,
                            content=str(content),
                            message_type="text",
                        ))
            except (json.JSONDecodeError, KeyError):
                continue

        return messages

    def _extract_from_stdout(self, stdout: str) -> list[AgentMessage]:
        """Fallback: try to find structured output in stdout."""
        messages: list[AgentMessage] = []

        # mini-swe-agent stdout typically has:
        #  ── Step N ── sections with model output
        # We split into step-based chunks
        import re

        # Try to find step markers: "Step", "###", etc.
        step_pattern = re.compile(
            r"(?:^|\n)(?:─+\s*Step\s+\d+\s*─+|###\s*Step\s+\d+|"
            r"={3,}\s*Step\s+\d+\s*={3,})(.*?)(?=\n(?:─+\s*Step\s+\d+|"
            r"###\s*Step\s+\d+|={3,}\s*Step\s+\d+)|$)",
            re.DOTALL,
        )
        steps = step_pattern.findall(stdout)

        if steps:
            for i, step_content in enumerate(steps):
                step_content = step_content.strip()
                if step_content:
                    messages.append(AgentMessage(
                        role="assistant",
                        content=step_content,
                        message_type="text",
                        metadata={"step": i + 1},
                    ))
        else:
            # No step markers found, return as a single message
            if stdout.strip():
                messages.append(AgentMessage(
                    role="agent",
                    content=stdout.strip(),
                    message_type="text",
                ))

        return messages
