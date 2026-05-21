"""OpenCode agent message extractor — parses OpenCode CLI output."""

import json
import re
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class OpenCodeExtractor(BaseExtractor):
    """Parse OpenCode agent output.

    OpenCode outputs a chat-like format. We parse messages from stdout
    by looking for structured sections and diff blocks.
    """

    agent_type = "opencode"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        messages: list[AgentMessage] = []

        if stdout_path.exists():
            messages = self._extract_from_stdout(stdout_path.read_text(errors="replace"))

        return messages

    def _extract_from_stdout(self, stdout: str) -> list[AgentMessage]:
        messages: list[AgentMessage] = []

        # Try JSON-lines format first (some versions output JSON events)
        json_messages = self._try_jsonl(stdout)
        if json_messages:
            return json_messages

        # Try to split by role markers or step markers
        # OpenCode may output sections like:
        #   "Thinking: ..."
        #   "Action: ..."
        #   "```diff ...```"
        sections = re.split(
            r"\n(?=(?:Thinking|Action|Observation|Response|Step)\s*\d*[:：])",
            stdout,
        )

        if len(sections) > 1:
            for section in sections:
                section = section.strip()
                if not section:
                    continue

                role = "assistant"
                if re.match(r"Thinking", section, re.IGNORECASE):
                    role = "thinking"
                elif re.match(r"Action", section, re.IGNORECASE):
                    role = "tool_call"
                elif re.match(r"Observation", section, re.IGNORECASE):
                    role = "tool_result"

                messages.append(AgentMessage(
                    role=role,
                    content=section,
                    message_type="text",
                ))
        else:
            # Single large output — strip ANSI and return as one message
            clean = self._strip_ansi(stdout).strip()
            if clean:
                messages.append(AgentMessage(
                    role="agent",
                    content=clean,
                    message_type="text",
                ))

        return messages

    def _try_jsonl(self, stdout: str) -> list[AgentMessage] | None:
        """Try to parse as JSON-lines format."""
        lines = stdout.splitlines()
        parsed = []
        for line in lines[:500]:  # Check first 500 lines
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict) and ("role" in data or "type" in data):
                    role = data.get("role") or data.get("type", "unknown")
                    content = data.get("content", data.get("text", ""))
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") if isinstance(c, dict) else str(c)
                            for c in content
                        )
                    if content:
                        parsed.append(AgentMessage(
                            role=str(role),
                            content=str(content),
                            timestamp=data.get("timestamp"),
                            message_type="text",
                        ))
                else:
                    return None  # Not JSONL chat format
            except json.JSONDecodeError:
                return None  # Not JSON at all

        return parsed if parsed else None

    @staticmethod
    def _strip_ansi(text: str) -> str:
        ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
        return ansi_escape.sub("", text)
