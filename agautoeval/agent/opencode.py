"""OpenCode agent adapter - wraps the opencode CLI."""

import os
import re
import shlex
import subprocess
import time

from agautoeval.agent.base import AgentResult, BaseAgent

_DIFF_RE = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)


class OpenCodeAgent(BaseAgent):
    """Adapter for the OpenCode CLI agent.

    In container mode (primary), the executor delegates to build_command()
    and ensure_runtime() / install logic. The standalone run() method is
    preserved for testing without Docker.
    """

    def __init__(
        self,
        command: str,
        env: dict[str, str] | None = None,
        timeout: int = 1800,
        install_cmd: str | None = None,
        version_cmd: str | None = None,
    ):
        super().__init__(command, env=env, timeout=timeout)
        self.install_cmd = install_cmd or ""
        self.version_cmd = version_cmd or ""

    def build_command(self, problem_statement: str) -> list[str]:
        """Build the docker exec command.

        Resolves {problem_statement} with shell quoting and wraps in bash -c.
        """
        cmd_str = self.command
        if "{problem_statement}" in cmd_str:
            cmd_str = cmd_str.replace(
                "{problem_statement}", shlex.quote(problem_statement),
            )
        return ["bash", "-c", cmd_str]

    def get_install_cmd(self) -> str | None:
        return self.install_cmd or None

    def get_version_cmd(self) -> str | None:
        return self.version_cmd or None

    def ensure_runtime(self, sandbox) -> None:
        """Ensure npm is available before installing the agent."""
        if self.install_cmd and "npm" in self.install_cmd:
            sandbox.ensure_npm()

    def post_install(self, sandbox) -> None:
        """Post-install steps (e.g., re-symlink nvm bins for npm)."""
        if self.install_cmd and "npm" in self.install_cmd:
            sandbox._symlink_nvm_bins()

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
