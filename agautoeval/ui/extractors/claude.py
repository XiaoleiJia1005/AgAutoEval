"""Claude Code message extractor — parses stream-json and JSONL session logs."""

import json
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class ClaudeCodeExtractor(BaseExtractor):
    """Parse Claude Code output (stream-json stdout or JSONL session logs)."""

    agent_type = "claude"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        if persist_dir:
            messages = self._extract_from_persist(persist_dir)
            if messages:
                return messages

        content = self._read_file(stdout_path)
        if content:
            return self._extract_from_stream(content)
        return []

    def _extract_from_persist(self, persist_dir: Path) -> list[AgentMessage]:
        projects_dir = persist_dir / "projects"
        if not projects_dir.is_dir():
            return []

        newest = self._find_most_recent(projects_dir, ["*.jsonl"])
        if not newest:
            return []

        messages: list[AgentMessage] = []
        try:
            with newest.open(errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = self._parse_jsonl_event(json.loads(line))
                        if msg:
                            messages.append(msg)
                    except json.JSONDecodeError:
                        continue
        except (FileNotFoundError, PermissionError):
            pass

        return messages

    def _parse_jsonl_event(self, event: dict) -> AgentMessage | None:
        event_type = event.get("type", "")
        msg = event.get("message", {})

        if event_type in ("user", "human"):
            content = self._flatten_content(msg.get("content", ""))
            return AgentMessage(
                role="user",
                content=content,
                timestamp=event.get("timestamp"),
            )

        if event_type == "assistant":
            content = self._parse_assistant_content(msg)
            return AgentMessage(
                role="assistant",
                content=content,
                timestamp=event.get("timestamp"),
            )

        return None

    def _parse_assistant_content(self, msg: dict) -> str:
        """Parse assistant message content, extracting tool calls inline."""
        content = msg.get("content", "")
        if not isinstance(content, list):
            return str(content) if content else ""

        parts: list[str] = []
        for c in content:
            ctype = c.get("type", "")
            if ctype == "text":
                parts.append(c.get("text", ""))
            elif ctype == "tool_use":
                parts.append(
                    f"[tool: {c.get('name', '')}]\n"
                    f"{json.dumps(c.get('input', {}), indent=2)}"
                )
        return "\n".join(parts)

    def _extract_from_stream(self, stdout: str) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        current_text: list[str] = []
        current_role = "assistant"

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            ev_type = event.get("type", "")

            if ev_type == "stream_event":
                self._handle_stream_event(event, current_text)
            elif ev_type == "assistant":
                msg = event.get("message", {})
                content = self._parse_assistant_content(msg)
                if content:
                    messages.append(AgentMessage(
                        role="assistant",
                        content=content,
                        timestamp=event.get("timestamp"),
                    ))
            elif ev_type == "user":
                msg = event.get("message", {})
                content = self._flatten_content(msg.get("content", ""))
                messages.append(AgentMessage(
                    role="user",
                    content=content,
                    timestamp=event.get("timestamp"),
                ))

        if current_text:
            messages.append(AgentMessage(
                role=current_role,
                content="".join(current_text),
            ))

        return messages

    def _handle_stream_event(self, event: dict, current_text: list[str]) -> None:
        """Process a stream_event, appending text to current_text."""
        inner = event.get("event", {})
        inner_type = inner.get("type", "")

        if inner_type == "content_block_delta":
            delta = inner.get("delta", {})
            if delta.get("type") == "text_delta":
                current_text.append(delta.get("text", ""))
            elif delta.get("type") == "input_json_delta":
                current_text.append(delta.get("partial_json", ""))
        elif inner_type == "content_block_start":
            block = inner.get("content_block", {})
            if block.get("type") == "tool_use":
                current_text.append(f"\n[tool: {block.get('name', '')}]\n")
        elif inner_type == "content_block_stop":
            pass
