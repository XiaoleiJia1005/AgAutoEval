"""Claude Code message extractor — parses stream-json and JSONL session logs."""

import json
from pathlib import Path

from agautoeval.ui.extractors import AgentMessage, BaseExtractor


class ClaudeCodeExtractor(BaseExtractor):
    """Parse Claude Code output.

    In container mode with --output-format stream-json, stdout contains
    JSON lines with stream events. Session logs at ~/.claude/projects/
    contain cleaner JSONL messages. We try both sources.
    """

    agent_type = "claude"

    def extract(
        self, stdout_path: Path, persist_dir: Path | None = None
    ) -> list[AgentMessage]:
        messages: list[AgentMessage] = []

        # 1. Try persisted JSONL session logs first (cleaner format)
        if persist_dir:
            messages = self._extract_from_persist(persist_dir)

        # 2. Fall back to stdout stream-json
        if not messages and stdout_path.exists():
            messages = self._extract_from_stream(stdout_path.read_text(errors="replace"))

        return messages

    def _extract_from_persist(self, persist_dir: Path) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        projects_dir = persist_dir / "projects"
        if not projects_dir.is_dir():
            return messages

        # Find the most recent JSONL session file
        jsonl_files: list[Path] = []
        for proj_dir in projects_dir.iterdir():
            if proj_dir.is_dir():
                for f in proj_dir.glob("*.jsonl"):
                    jsonl_files.append(f)

        if not jsonl_files:
            return messages

        # Sort by modification time, use the most recent
        jsonl_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for line in jsonl_files[0].read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                msg = self._parse_jsonl_event(event)
                if msg:
                    messages.append(msg)
            except json.JSONDecodeError:
                continue

        return messages

    def _parse_jsonl_event(self, event: dict) -> AgentMessage | None:
        event_type = event.get("type", "")
        msg = event.get("message", {})

        if event_type in ("user", "human"):
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if c.get("type") == "text"
                )
            return AgentMessage(
                role="user",
                content=content,
                timestamp=event.get("timestamp"),
                message_type="text",
            )

        if event_type == "assistant":
            content = msg.get("content", "")
            if isinstance(content, list):
                parts: list[str] = []
                for c in content:
                    if c.get("type") == "text":
                        parts.append(c.get("text", ""))
                    elif c.get("type") == "tool_use":
                        parts.append(
                            f"[tool: {c.get('name', '')}]\n{json.dumps(c.get('input', {}), indent=2)}"
                        )
                content = "\n".join(parts)
            return AgentMessage(
                role="assistant",
                content=content,
                timestamp=event.get("timestamp"),
                message_type="text",
            )

        return None

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
                        current_text.append(
                            f"\n[tool: {block.get('name', '')}]\n"
                        )

                elif inner_type == "content_block_stop":
                    if current_text:
                        messages.append(AgentMessage(
                            role=current_role,
                            content="".join(current_text),
                            message_type="text",
                        ))
                        current_text = []

            elif ev_type == "assistant":
                msg = event.get("message", {})
                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for c in content:
                        if c.get("type") == "text":
                            parts.append(c.get("text", ""))
                        elif c.get("type") == "tool_use":
                            parts.append(
                                f"[tool: {c.get('name', '')}]\n"
                                f"{json.dumps(c.get('input', {}), indent=2)}"
                            )
                    content = "\n".join(parts)
                if content:
                    messages.append(AgentMessage(
                        role="assistant",
                        content=str(content),
                        timestamp=event.get("timestamp"),
                        message_type="text",
                    ))

            elif ev_type == "user":
                msg = event.get("message", {})
                messages.append(AgentMessage(
                    role="user",
                    content=str(msg.get("content", "")),
                    timestamp=event.get("timestamp"),
                    message_type="text",
                ))

        # Flush remaining text
        if current_text:
            messages.append(AgentMessage(
                role=current_role,
                content="".join(current_text),
                message_type="text",
            ))

        return messages
