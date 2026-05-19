"""Docker sandbox for per-task isolated execution.

Each task runs in its own Docker container. The container provides:
- Isolated filesystem (repo clone, agent modifications, test runs)
- Isolated Python environment (pip installs, dependencies)
- Clean teardown after task completion

Evaluation follows the SWE-bench protocol:
  - Run FAIL_TO_PASS tests → all must now pass
  - Run PASS_TO_PASS tests → all must still pass
  - Resolved = both conditions hold
"""

import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from agautoeval.dataset import Task


@dataclass
class SandboxResult:
    test_output: str = ""
    passed: bool = False
    error: str = ""
    duration: float = 0.0
    logs: dict[str, str] = field(default_factory=dict)

    # SWE-bench specific fields
    f2p_total: int = 0
    f2p_passed: int = 0
    p2p_total: int = 0
    p2p_passed: int = 0
    f2p_failures: list[str] = field(default_factory=list)
    p2p_failures: list[str] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        """SWE-bench resolution: all F2P pass AND all P2P pass."""
        if self.f2p_total == 0 and self.p2p_total == 0:
            return self.passed
        return self.f2p_passed == self.f2p_total and self.p2p_passed == self.p2p_total


class DockerSandbox:
    """Per-task Docker container for fully isolated agent execution."""

    def __init__(
        self,
        image: str,
        timeout: int = 600,
        mode: str = "auto",
        repo_path: str = "/repo",
        setup_commands: list[str] | None = None,
        cleanup_image: bool = False,
    ):
        self.image = image
        self.timeout = timeout
        self.mode = mode
        self.repo_path = repo_path
        self.setup_commands = setup_commands or []
        self.cleanup_image = cleanup_image
        self._container_name: str | None = None
        self._created: bool = False

    # ── lifecycle ──────────────────────────────────────────────────

    def prepare(self, task: Task) -> SandboxResult:
        """Create container, set up repo (clone or use prebuilt)."""
        logs: dict[str, str] = {}
        start = time.monotonic()
        self._container_name = f"agautoeval_{task.instance_id}"

        try:
            self._exec_host(
                [
                    "docker", "run", "-d", "--rm",
                    "--name", self._container_name,
                    "-w", self.repo_path,
                    self.image,
                    "sleep", "infinity",
                ],
                timeout=30,
            )
            self._created = True

            if self.mode == "prebuilt":
                self._prepare_prebuilt(task, logs)
            else:
                self._prepare_auto(task, logs)

            return SandboxResult(
                passed=True,
                duration=time.monotonic() - start,
                logs=logs,
            )
        except subprocess.CalledProcessError as e:
            return SandboxResult(
                passed=False,
                error=f"Failed to prepare sandbox: {e}\nstderr: {e.stderr}",
                duration=time.monotonic() - start,
                logs=logs,
            )
        except Exception as e:
            return SandboxResult(
                passed=False,
                error=f"Failed to prepare sandbox: {e}",
                duration=time.monotonic() - start,
                logs=logs,
            )

    def _prepare_auto(self, task: Task, logs: dict) -> None:
        """Auto mode: install tools, clone repo, install package."""
        install_cmd = (
            "apt-get update -qq && apt-get install -y -qq git 2>&1 && "
            "pip install -q pytest 2>&1"
        )
        for sc in self.setup_commands:
            install_cmd += f" && {sc}"
        logs["install_tools"] = self.exec(
            ["bash", "-c", install_cmd], cwd="/"
        )[0]

        if task.repo.startswith("file://") or task.repo.startswith("/"):
            self._prepare_repo_via_host(task, logs)
        else:
            self._prepare_repo_in_container(task, logs)

        logs["install_repo"] = self.exec(
            ["bash", "-c",
             f"pip install -q -e {self.repo_path} 2>&1 || pip install -q {self.repo_path} 2>&1"],
            cwd=self.repo_path,
        )[0]

    def _prepare_prebuilt(self, task: Task, logs: dict) -> None:
        """Prebuilt mode: repo and deps already in image. Only apply test_patch."""
        if task.test_patch:
            logs["apply_test_patch"] = self.exec(
                ["git", "apply", "-"],
                cwd=self.repo_path, stdin=task.test_patch,
            )[0]
        # Run any setup_commands (e.g., pip install pytest if missing)
        if self.setup_commands:
            cmds = " && ".join(self.setup_commands)
            logs["setup"] = self.exec(
                ["bash", "-c", cmds], cwd=self.repo_path,
            )[0]

    def cleanup(self) -> None:
        """Stop container and optionally remove image."""
        if not self._created or not self._container_name:
            return
        try:
            subprocess.run(
                ["docker", "stop", self._container_name],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass
        # Container is auto-removed (--rm), now optionally remove image
        if self.cleanup_image:
            try:
                subprocess.run(
                    ["docker", "rmi", self.image],
                    capture_output=True,
                    timeout=30,
                )
            except Exception:
                pass

    def _prepare_repo_via_host(self, task: Task, logs: dict) -> None:
        import tempfile
        host_dir = tempfile.mkdtemp(prefix="agautoeval_")
        try:
            host_repo = str(Path(host_dir) / "repo")
            self._exec_host(["git", "clone", task.repo, host_repo], timeout=120)
            self._exec_host(
                ["git", "checkout", task.base_commit],
                cwd=host_repo, timeout=60,
            )
            logs["clone"] = "cloned on host"
            logs["checkout"] = f"checked out {task.base_commit}"
            self._exec_host(
                ["docker", "cp", f"{host_repo}/.", f"{self._container_name}:{self.repo_path}"],
                timeout=60,
            )
            if task.test_patch:
                patch_out = self.exec(
                    ["git", "apply", "-"],
                    cwd=self.repo_path, stdin=task.test_patch,
                )
                logs["apply_test_patch"] = patch_out[0]
        finally:
            shutil.rmtree(host_dir, ignore_errors=True)

    def _prepare_repo_in_container(self, task: Task, logs: dict) -> None:
        clone_out = self.exec(["git", "clone", task.repo, self.repo_path], cwd="/")
        logs["clone"] = clone_out[0]
        checkout_out = self.exec(
            ["git", "checkout", task.base_commit], cwd=self.repo_path,
        )
        logs["checkout"] = checkout_out[0]
        if task.test_patch:
            patch_out = self.exec(
                ["git", "apply", "-"],
                cwd=self.repo_path, stdin=task.test_patch,
            )
            logs["apply_test_patch"] = patch_out[0]

    # ── command execution ──────────────────────────────────────────

    def exec(
        self,
        cmd: list[str],
        cwd: str | None = None,
        stdin: str | None = None,
        timeout: int | None = None,
    ) -> Tuple[str, str, int]:
        """Execute a command inside the Docker container.

        Returns (stdout, stderr, returncode).
        Does NOT raise on non-zero returncode — caller decides.
        """
        docker_cmd = ["docker", "exec", "-i"]
        if cwd:
            docker_cmd.extend(["-w", cwd])
        docker_cmd.append(self._container_name)
        docker_cmd.extend(cmd)

        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout or self.timeout,
            input=stdin,
        )
        return result.stdout, result.stderr, result.returncode

    def exec_check(
        self,
        cmd: list[str],
        cwd: str | None = None,
        stdin: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Execute a command inside the container. Raises on failure."""
        stdout, stderr, rc = self.exec(cmd, cwd=cwd, stdin=stdin, timeout=timeout)
        if rc != 0:
            raise subprocess.CalledProcessError(
                rc, cmd, output=stdout, stderr=stderr
            )
        return stdout

    # ── agent ──────────────────────────────────────────────────────

    def run_agent_command(
        self,
        agent_cmd: list[str],
        problem_statement: str,
        timeout: int | None = None,
    ) -> Tuple[str, str, int, float]:
        """Run agent inside the container. Returns (stdout, stderr, rc, duration)."""
        start = time.monotonic()
        stdout, stderr, rc = self.exec(
            agent_cmd,
            cwd=self.repo_path,
            stdin=problem_statement,
            timeout=timeout or self.timeout,
        )
        return stdout, stderr, rc, time.monotonic() - start

    def apply_patch(self, patch: str) -> SandboxResult:
        """Apply the agent's patch inside the container."""
        start = time.monotonic()
        if not patch.strip():
            return SandboxResult(passed=False, error="Empty patch", duration=0.0)
        try:
            self.exec_check(
                ["git", "apply", "--verbose", "-"],
                cwd=self.repo_path, stdin=patch,
            )
            return SandboxResult(passed=True, duration=time.monotonic() - start)
        except subprocess.CalledProcessError as e:
            return SandboxResult(
                passed=False,
                error=f"Failed to apply patch: stdout={e.stdout} stderr={e.stderr}",
                duration=time.monotonic() - start,
            )

    # ── test evaluation (SWE-bench protocol) ───────────────────────

    def evaluate(
        self,
        fail_to_pass: list[str],
        pass_to_pass: list[str],
        timeout: int | None = None,
    ) -> SandboxResult:
        """Run the SWE-bench evaluation protocol.

        1. Run every FAIL_TO_PASS test → must pass
        2. Run every PASS_TO_PASS test → must pass
        3. resolved = all F2P pass AND all P2P pass
        """
        start = time.monotonic()
        timeout = timeout or self.timeout

        f2p_passed, f2p_failures = self._run_test_list(
            fail_to_pass, expect_pass=True, timeout=timeout,
        )
        p2p_passed, p2p_failures = self._run_test_list(
            pass_to_pass, expect_pass=True, timeout=timeout,
        )

        f2p_total = len(fail_to_pass)
        p2p_total = len(pass_to_pass)

        all_output_parts: list[str] = []
        if f2p_failures:
            all_output_parts.append(
                f"FAIL_TO_PASS failures ({f2p_passed}/{f2p_total}):\n"
                + "\n".join(f"  FAIL: {t}" for t in f2p_failures)
            )
        if p2p_failures:
            all_output_parts.append(
                f"PASS_TO_PASS failures ({p2p_passed}/{p2p_total}):\n"
                + "\n".join(f"  FAIL: {t}" for t in p2p_failures)
            )
        if not f2p_failures and not p2p_failures:
            all_output_parts.append(
                f"All tests passed: {f2p_total} F2P + {p2p_total} P2P"
            )

        return SandboxResult(
            test_output="\n".join(all_output_parts),
            f2p_total=f2p_total,
            f2p_passed=f2p_passed,
            p2p_total=p2p_total,
            p2p_passed=p2p_passed,
            f2p_failures=f2p_failures,
            p2p_failures=p2p_failures,
            # resolved is computed by the property
            duration=time.monotonic() - start,
        )

    def _run_test_list(
        self,
        tests: list[str],
        expect_pass: bool,
        timeout: int,
    ) -> Tuple[int, list[str]]:
        """Run a list of pytest specifiers, return (passed_count, [failed_test_names]).

        Handles both formats:
          - Full path:  "tests/test_foo.py::TestBar::test_baz"
          - Bare name:  "test_baz"  → uses pytest -k
        """
        passed = 0
        failures: list[str] = []

        for test_spec in tests:
            if "::" in test_spec or "/" in test_spec:
                cmd = ["python", "-m", "pytest", "-q", "--tb=no", test_spec]
            else:
                cmd = ["python", "-m", "pytest", "-q", "--tb=no", "-k", test_spec]

            stdout, stderr, rc = self.exec(cmd, cwd=self.repo_path, timeout=timeout)

            if rc == 0:
                passed += 1
            else:
                failures.append(test_spec)

        return passed, failures

    # ── internal helpers ───────────────────────────────────────────

    @staticmethod
    def _exec_host(
        cmd: list[str],
        timeout: int = 30,
        stdin: str | None = None,
        cwd: str | None = None,
    ) -> Tuple[str, str]:
        """Run a command on the host (used for docker commands themselves)."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=stdin,
            cwd=cwd,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                cmd,
                output=result.stdout,
                stderr=result.stderr,
            )
        return result.stdout, result.stderr
