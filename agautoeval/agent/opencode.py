"""OpenCode agent adapter - wraps the opencode CLI."""

import os
import re
import subprocess
import time

from agautoeval.agent.base import AgentResult, BaseAgent
from agautoeval.agent.utils import ensure_npm, symlink_nvm_bins

_DIFF_RE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)


class OpenCodeAgent(BaseAgent):
    """Adapter for the OpenCode CLI agent."""

    def __init__(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: int = 1800,
        install_cmd: str | None = None,
        version_cmd: str | None = None,
        model: str = "",
        provider: str = "",
    ):
        super().__init__(command, env=env, timeout=timeout, model=model, provider=provider)
        self.install_cmd = install_cmd or ""
        self.version_cmd = version_cmd or ""

    def get_install_cmd(self) -> str | None:
        return self.install_cmd or None

    def get_version_cmd(self) -> str | None:
        return self.version_cmd or None

    def ensure_runtime(self, sandbox) -> None:
        if self.install_cmd and "npm" in self.install_cmd:
            ensure_npm(sandbox)

    def post_install(self, sandbox) -> None:
        if self.install_cmd and "npm" in self.install_cmd:
            symlink_nvm_bins(sandbox)

    def run(self, repo_path: str, problem_statement: str) -> AgentResult:
        cmd_str = self._resolve_command(problem_statement)
        env = {**os.environ, **self._env}
        start = time.monotonic()

        try:
            proc = subprocess.run(
                ["bash", "-c", cmd_str],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
                cwd=repo_path,
            )
            stdout = proc.stdout
            stderr = proc.stderr

            return AgentResult(
                patch=self._extract_patch(stdout),
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

    @staticmethod
    def _extract_patch(stdout: str) -> str:
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
