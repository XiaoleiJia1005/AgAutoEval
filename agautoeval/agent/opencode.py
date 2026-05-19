"""OpenCode agent adapter - wraps the opencode CLI."""

import os
import re
import subprocess
import time

from agautoeval.agent.base import AgentResult, BaseAgent

_DIFF_RE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)


class OpenCodeAgent(BaseAgent):
    """Adapter for the OpenCode CLI agent."""

    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        cmd = [
            self.command,
            "run",
            problem_statement,
        ]

        env = {**os.environ, **self.env}
        start = time.monotonic()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=repo_path,
            )
            stdout = proc.stdout
            stderr = proc.stderr

            patch = self._extract_patch(stdout)

            return AgentResult(
                patch=patch,
                stdout=stdout,
                stderr=stderr,
                duration=time.monotonic() - start,
                success=True,
            )
        except subprocess.TimeoutExpired as e:
            return AgentResult(
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                duration=time.monotonic() - start,
                success=False,
                error=f"Agent timed out after {self.timeout}s",
            )
        except Exception as e:
            return AgentResult(
                duration=time.monotonic() - start,
                success=False,
                error=str(e),
            )

    def _extract_patch(self, stdout: str) -> str:
        """Extract unified diff from agent output."""
        m = _DIFF_RE.search(stdout)
        if m:
            return m.group(1).strip()

        lines = stdout.splitlines()
        diff_lines: list[str] = []
        in_diff = False
        for line in lines:
            if line.startswith("diff ") or line.startswith("---") or line.startswith("+++"):
                in_diff = True
            if in_diff:
                diff_lines.append(line)
        if diff_lines:
            return "\n".join(diff_lines)

        return stdout.strip()
