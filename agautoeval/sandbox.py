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
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from agautoeval.dataset import Task


def check_docker() -> None:
    """Verify Docker CLI is available and daemon is reachable. Exits if not."""
    if shutil.which("docker") is None:
        print("ERROR: Docker is not installed. Install Docker and try again.")
        sys.exit(1)
    try:
        subprocess.run(
            ["docker", "info"], capture_output=True, timeout=10, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print("ERROR: Docker daemon is not running or unreachable. Start Docker and try again.")
        sys.exit(1)


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
    f2p_failure_details: dict[str, str] = field(default_factory=dict)
    p2p_failure_details: dict[str, str] = field(default_factory=dict)

    @property
    def resolved(self) -> bool:
        """SWE-bench resolution: all F2P pass AND all P2P pass."""
        if self.f2p_total == 0 and self.p2p_total == 0:
            return True  # vacuous: no tests → all pass
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
        auto_pull_image: bool = True,
        mounts: list[tuple[str, str, str]] | None = None,
        log=print,
    ):
        self.image = image
        self.timeout = timeout
        self.mode = mode
        self.repo_path = repo_path
        self.setup_commands = setup_commands or []
        self.cleanup_image = cleanup_image
        self.auto_pull_image = auto_pull_image
        self.mounts = mounts or []
        self._log = log
        self._container_name: str | None = None
        self._created: bool = False

    # ── lifecycle ──────────────────────────────────────────────────

    def _ensure_image(self) -> None:
        """Check if the image exists locally; pull if configured and missing."""
        inspect = subprocess.run(
            ["docker", "image", "inspect", self.image],
            capture_output=True, text=True,
        )
        if inspect.returncode == 0:
            return  # image exists

        if not self.auto_pull_image:
            raise RuntimeError(
                f"Image '{self.image}' not found locally and auto_pull_image is disabled."
                f"\n  Pull it manually: docker pull {self.image}"
            )

        self._log(f"Pulling image: {self.image}")
        result = subprocess.run(
            ["docker", "pull", self.image],
            capture_output=False, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to pull image '{self.image}' (exit code {result.returncode})")

    def ensure_npm(self, min_version: str = "18") -> None:
        """Ensure npm (via nvm-managed Node.js) is available inside the container.

        Checks for npm; if missing, installs nvm then uses it to install
        Node.js >= *min_version*. The node/npm binaries are symlinked to
        /usr/local/bin so subsequent exec() calls find them on PATH.
        """
        # Check if npm already exists
        _, _, rc = self.exec(["which", "npm"], cwd="/", timeout=30)
        if rc == 0:
            return

        self._log(f"[{self._container_name}] npm not found, installing nvm + Node.js {min_version}...")

        # ── Install curl if needed for nvm installer ───────────
        NVM_DIR = "/root/.nvm"
        NVM_INSTALL_SCRIPT = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh"

        self.exec(
            ["bash", "-c", "which curl || (apt-get update -qq && apt-get install -y -qq curl)"],
            cwd="/", timeout=120,
        )

        # ── Install nvm ────────────────────────────────────────
        stdout, _, rc = self.exec(
            ["bash", "-c", f"test -d {NVM_DIR} && echo '1' || echo '0'"],
            cwd="/", timeout=10,
        )
        if stdout.strip() != "1":
            self._log(f"[{self._container_name}] Downloading nvm...")
            self.exec(
                ["bash", "-c",
                 f"(curl -fsSL {NVM_INSTALL_SCRIPT} || wget -qO- {NVM_INSTALL_SCRIPT}) | bash"],
                cwd="/", timeout=120,
            )

        # ── Install Node.js via nvm ────────────────────────────
        self._log(f"[{self._container_name}] Installing Node.js {min_version} via nvm...")
        self.exec(
            ["bash", "-c",
             f'export NVM_DIR="{NVM_DIR}" && '
             f'[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
             f'nvm install {min_version} && '
             f'nvm alias default {min_version}'],
            cwd="/", timeout=300,
        )
        self._symlink_nvm_bins(NVM_DIR)

        # ── Verify ─────────────────────────────────────────────
        stdout, _, rc = self.exec(["node", "--version"], cwd="/", timeout=30)
        if rc == 0:
            npm_ver, _, _ = self.exec(["npm", "--version"], cwd="/", timeout=30)
            self._log(f"[{self._container_name}] Node.js {stdout.strip()}, npm {npm_ver.strip()}")
        else:
            raise RuntimeError("Node.js installation via nvm failed")

    def _symlink_nvm_bins(self, nvm_dir: str = "/root/.nvm") -> None:
        """Symlink all executables from the nvm default version bin dir to
        /usr/local/bin so non-interactive docker exec shells can find them.
        """
        self.exec(
            ["bash", "-c",
             f'export NVM_DIR="{nvm_dir}" && '
             f'[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
             f'BIN_DIR=$(dirname "$(nvm which default)") && '
             f'for f in "$BIN_DIR"/*; do '
             f'  [ -f "$f" ] && [ -x "$f" ] && ln -sf "$f" /usr/local/bin/$(basename "$f"); '
             f'done'],
            cwd="/", timeout=30,
        )

    def prepare(self, task: Task) -> SandboxResult:
        """Create container, set up repo (clone or use prebuilt)."""
        logs: dict[str, str] = {}
        start = time.monotonic()
        self._container_name = f"agautoeval_{task.instance_id}"

        try:
            # Ensure the Docker image is available
            self._ensure_image()

            # Create host directories for bind mounts
            for host_path, _container_path, _mode in self.mounts:
                Path(host_path).mkdir(parents=True, exist_ok=True)

            # Build docker run command with bind mounts
            docker_cmd = [
                "docker", "run", "-d", "--rm",
                "--name", self._container_name,
                "-w", self.repo_path,
            ]
            for host_path, container_path, mode in self.mounts:
                docker_cmd.extend(["-v", f"{host_path}:{container_path}:{mode}"])
            docker_cmd.extend([self.image, "sleep", "infinity"])

            self._exec_host(docker_cmd, timeout=30)
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
        env: dict[str, str] | None = None,
    ) -> Tuple[str, str, int]:
        """Execute a command inside the Docker container.

        Returns (stdout, stderr, returncode).
        Does NOT raise on non-zero returncode — caller decides.
        """
        docker_cmd = ["docker", "exec", "-i"]
        if cwd:
            docker_cmd.extend(["-w", cwd])
        if env:
            for k, v in env.items():
                docker_cmd.extend(["-e", f"{k}={v}"])
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
        env: dict[str, str] | None = None,
    ) -> Tuple[str, str, int, float]:
        """Run agent inside the container. Returns (stdout, stderr, rc, duration)."""
        start = time.monotonic()
        stdout, stderr, rc = self.exec(
            agent_cmd,
            cwd=self.repo_path,
            stdin=problem_statement,
            timeout=timeout or self.timeout,
            env=env,
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

        f2p_passed, f2p_failures, f2p_details = self._run_test_list(
            fail_to_pass, expect_pass=True, timeout=timeout,
        )
        p2p_passed, p2p_failures, p2p_details = self._run_test_list(
            pass_to_pass, expect_pass=True, timeout=timeout,
        )

        f2p_total = len(fail_to_pass)
        p2p_total = len(pass_to_pass)

        all_output_parts: list[str] = []
        if f2p_failures:
            parts = [f"FAIL_TO_PASS failures ({f2p_passed}/{f2p_total}):"]
            for name in f2p_failures:
                detail = f2p_details.get(name, "")
                parts.append(f"  FAIL: {name}\n{detail}")
            all_output_parts.append("\n".join(parts))
        if p2p_failures:
            parts = [f"PASS_TO_PASS failures ({p2p_passed}/{p2p_total}):"]
            for name in p2p_failures:
                detail = p2p_details.get(name, "")
                parts.append(f"  FAIL: {name}\n{detail}")
            all_output_parts.append("\n".join(parts))
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
            f2p_failure_details=f2p_details,
            p2p_failure_details=p2p_details,
            duration=time.monotonic() - start,
        )

    def _run_test_list(
        self,
        tests: list[str],
        expect_pass: bool,
        timeout: int,
    ) -> tuple[int, list[str], dict[str, str]]:
        """Run a list of pytest specifiers.

        Returns (passed_count, [failed_test_names], {test_name: failure_output}).

        Runs all full-path specs together to avoid per-test collection noise,
        then re-runs only failures individually with --tb=short for details.
        """
        if not tests:
            return 0, [], {}

        passed = 0
        failures: list[str] = []
        failure_details: dict[str, str] = {}

        # Separate full-path specs (:: or /) from bare -k names
        path_tests = [t for t in tests if "::" in t or "/" in t]
        bare_tests = [t for t in tests if t not in path_tests]

        # ── Run full-path tests as a group ──────────────────────
        if path_tests:
            # First pass: --tb=no for fast pass/fail determination
            cmd = [
                "python", "-m", "pytest", "-v", "--tb=no",
                "--continue-on-collection-errors",
            ] + path_tests
            stdout, stderr, rc = self.exec(cmd, cwd=self.repo_path, timeout=timeout)

            # Parse verbose output: "test_spec PASSED|FAILED|ERROR [ N%]"
            failed_names = set()
            for line in stdout.splitlines():
                line = line.strip()
                if "FAILED" in line or "ERROR" in line:
                    # Extract test spec from line like "path::name FAILED [ 50%]"
                    test_name = line.rsplit("FAILED", 1)[0].rsplit("ERROR", 1)[0].strip()
                    if test_name:
                        failed_names.add(test_name)

            for t in path_tests:
                if t in failed_names:
                    failures.append(t)
                else:
                    passed += 1

            # Second pass: re-run only failures with --tb=short for details
            if failed_names:
                detail_cmd = [
                    "python", "-m", "pytest", "-v", "--tb=short",
                    "--continue-on-collection-errors",
                ] + list(failed_names)
                d_stdout, d_stderr, _ = self.exec(
                    detail_cmd, cwd=self.repo_path, timeout=timeout,
                )
                # Split output per test: each section starts with the test spec line
                current_test = None
                current_lines: list[str] = []
                for line in d_stdout.splitlines():
                    # Detect test result lines like "path::name FAILED [ N%]"
                    stripped = line.strip()
                    if any(marker in stripped for marker in (" PASSED", " FAILED", " ERROR")):
                        if current_test and current_lines:
                            failure_details[current_test] = "\n".join(current_lines)
                        for marker in (" PASSED", " FAILED", " ERROR"):
                            if marker in stripped:
                                current_test = stripped.rsplit(marker, 1)[0].strip()
                                break
                        current_lines = [line]
                    else:
                        current_lines.append(line)
                # Flush last test
                if current_test and current_lines:
                    failure_details[current_test] = "\n".join(current_lines)

        # ── Run bare-name tests individually ────────────────────
        for test_spec in bare_tests:
            cmd = ["python", "-m", "pytest", "-q", "--tb=short", "-k", test_spec]
            stdout, stderr, rc = self.exec(cmd, cwd=self.repo_path, timeout=timeout)
            if rc == 0:
                passed += 1
            else:
                failures.append(test_spec)
                failure_details[test_spec] = (
                    stdout.strip()
                    + ("\n" + stderr.strip() if stderr.strip() else "")
                )

        return passed, failures, failure_details

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
