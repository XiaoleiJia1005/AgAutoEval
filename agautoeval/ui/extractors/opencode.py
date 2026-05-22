"""OpenCode agent message extractor — parses OpenCode CLI output."""

import json
import re
from itertools import islice
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class OpenCodeExtractor(BaseExtractor):
    """Parse OpenCode agent output from stdout."""

    agent_type = "opencode"

    _SECTION_RE = re.compile(
        r"\n(?=(?:Thinking|Action|Observation|Response|Step)\s*\d*[:：])",
    )
    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        content = self._read_file(stdout_path)
        if not content:
            return []

        json_msgs = self._try_jsonl(content)
        if json_msgs:
            return json_msgs

        return self._extract_sections(content)

    def _try_jsonl(self, stdout: str) -> list[AgentMessage] | None:
        """Try to parse as JSON-lines format. Returns None if not JSONL."""
        messages: list[AgentMessage] = []
        any_json = False

        for line in islice(stdout.splitlines(), 500):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                if any_json:
                    return messages  # mixed JSON/non-JSON — stop here
                return None  # not JSON at all

            any_json = True
            if isinstance(data, dict) and ("role" in data or "type" in data):
                role = str(data.get("role") or data.get("type", "unknown"))
                content = self._flatten_content(
                    data.get("content", data.get("text", ""))
                )
                if content:
                    messages.append(AgentMessage(
                        role=role,
                        content=content,
                        timestamp=data.get("timestamp"),
                    ))
            else:
                return None  # valid JSON but not chat format

        return messages if messages else None

    def _extract_sections(self, stdout: str) -> list[AgentMessage]:
        sections = self._SECTION_RE.split(stdout)
        if len(sections) <= 1:
            clean = self._ANSI_RE.sub("", stdout).strip()
            if clean:
                return [AgentMessage(role="agent", content=clean)]
            return []

        messages: list[AgentMessage] = []
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
            messages.append(AgentMessage(role=role, content=section))
        return messages
