"""Concurrent task executor - the core evaluation pipeline.

Each task runs in its own Docker container. The container provides complete isolation:
- Agent executes inside the container
- All git operations inside the container
- Tests run inside the container
- Container is destroyed after task completion
"""

import time
import traceback
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from agautoeval.config import Config
from agautoeval.dataset import Task
from agautoeval.logger import TaskLogger
from agautoeval.sandbox import DockerSandbox


class TaskResult:
    """Result of a single task evaluation."""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.resolved: bool = False
        self.duration: float = 0.0
        self.error: str = ""
        self.agent_stdout: str = ""
        self.agent_stderr: str = ""
        self.test_output: str = ""
        self.sandbox_logs: dict[str, str] = {}
        self.agent_duration: float = 0.0
        # SWE-bench evaluation details
        self.f2p_total: int = 0
        self.f2p_passed: int = 0
        self.p2p_total: int = 0
        self.p2p_passed: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = {
            "instance_id": self.instance_id,
            "resolved": self.resolved,
            "duration": self.duration,
            "error": self.error,
            "agent_duration": self.agent_duration,
        }
        if self.f2p_total or self.p2p_total:
            d["f2p"] = f"{self.f2p_passed}/{self.f2p_total}"
            d["p2p"] = f"{self.p2p_passed}/{self.p2p_total}"
        return d


class Executor:
    """Runs evaluation tasks with per-task Docker isolation.

    Each task gets its own Docker container. The agent, patches, and tests
    all execute inside the container, providing complete environment isolation.
    """

    def __init__(self, config: Config, logger: TaskLogger):
        self.config = config
        self.logger = logger
        self.output_dir = Path(config.output.dir).resolve()

    def run(self, tasks: list[Task]) -> list[TaskResult]:
        results: list[TaskResult] = []
        max_workers = self.config.execution.max_workers

        self.logger.info(
            f"Running {len(tasks)} tasks with {max_workers} workers "
            f"(each in its own Docker container)"
        )

        if max_workers <= 1:
            for task in tqdm(tasks, desc="Evaluating", unit="task"):
                result = self._run_one(task)
                results.append(result)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures: dict[Future[TaskResult], str] = {}
                for task in tasks:
                    future = pool.submit(self._run_one, task)
                    futures[future] = task.instance_id

                with tqdm(total=len(tasks), desc="Evaluating", unit="task") as pbar:
                    for future in as_completed(futures):
                        instance_id = futures[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            result = TaskResult(instance_id)
                            result.error = str(e)
                            self.logger.error(f"Task {instance_id} crashed: {e}")
                        results.append(result)
                        pbar.update(1)

        return results

    def _run_one(self, task: Task) -> TaskResult:
        result = TaskResult(task.instance_id)
        start = time.monotonic()
        sb = DockerSandbox(
            image=self.config.sandbox.image,
            timeout=self.config.execution.timeout,
            setup_commands=self.config.sandbox.setup_commands,
        )

        try:
            # ── Step 1: Create container and prepare repo ──────────
            self.logger.info(f"[{task.instance_id}] Starting Docker container...")
            prep = sb.prepare(task)
            result.sandbox_logs = prep.logs

            for name, content in prep.logs.items():
                self.logger.write_task_log(
                    task.instance_id, f"sandbox_{name}.log", content
                )

            if not prep.passed:
                result.error = prep.error
                self.logger.error(f"[{task.instance_id}] Sandbox failed: {prep.error}")
                result.duration = time.monotonic() - start
                return result

            # ── Step 2: Run agent inside container ─────────────────
            self.logger.info(f"[{task.instance_id}] Running agent in container...")
            if self.config.agent.type == "mock":
                agent_stdout, agent_stderr, agent_rc, agent_dur = \
                    self._run_mock_agent(task)
            else:
                agent_cmd = self._build_agent_cmd(task.problem_statement)
                agent_stdout, agent_stderr, agent_rc, agent_dur = sb.run_agent_command(
                    agent_cmd,
                    task.problem_statement,
                    timeout=self.config.agent.timeout,
                )
            result.agent_stdout = agent_stdout
            result.agent_stderr = agent_stderr
            result.agent_duration = agent_dur

            self.logger.write_task_log(
                task.instance_id, "agent_stdout.log", agent_stdout
            )
            self.logger.write_task_log(
                task.instance_id, "agent_stderr.log", agent_stderr
            )

            if agent_rc != 0:
                result.error = f"Agent exited with code {agent_rc}"
                self.logger.error(f"[{task.instance_id}] {result.error}")
                result.duration = time.monotonic() - start
                return result

            # ── Step 3: Extract patch from agent output ────────────
            patch = self._extract_patch(agent_stdout)

            if not patch.strip():
                result.error = "Agent produced no patch"
                self.logger.warning(f"[{task.instance_id}] Empty patch")
                result.duration = time.monotonic() - start
                return result

            # ── Step 4: Apply patch inside container ───────────────
            self.logger.info(f"[{task.instance_id}] Applying patch...")
            patch_res = sb.apply_patch(patch)
            if not patch_res.passed:
                result.error = patch_res.error
                self.logger.write_task_log(
                    task.instance_id, "patch_error.log", patch_res.error
                )
                result.duration = time.monotonic() - start
                return result

            # ── Step 5: Evaluate (SWE-bench protocol) ────────────
            self.logger.info(
                f"[{task.instance_id}] Running evaluation "
                f"(F2P={len(task.fail_to_pass)}, P2P={len(task.pass_to_pass)})..."
            )
            test_res = sb.evaluate(task.fail_to_pass, task.pass_to_pass)
            result.test_output = test_res.test_output
            result.resolved = test_res.resolved
            result.f2p_total = test_res.f2p_total
            result.f2p_passed = test_res.f2p_passed
            result.p2p_total = test_res.p2p_total
            result.p2p_passed = test_res.p2p_passed

            self.logger.write_task_log(
                task.instance_id, "test_output.log", test_res.test_output
            )
            if test_res.f2p_failures:
                self.logger.write_task_log(
                    task.instance_id, "f2p_failures.log",
                    "\n".join(test_res.f2p_failures),
                )
            if test_res.p2p_failures:
                self.logger.write_task_log(
                    task.instance_id, "p2p_failures.log",
                    "\n".join(test_res.p2p_failures),
                )

            self.logger.info(
                f"[{task.instance_id}] "
                + ("RESOLVED" if result.resolved else "UNRESOLVED")
            )

        except Exception as e:
            result.error = str(e)
            self.logger.error(
                f"[{task.instance_id}] Exception: {traceback.format_exc()}"
            )
            self.logger.write_task_log(task.instance_id, "error.log", str(e))

        finally:
            # ── Cleanup: destroy container ─────────────────────────
            self.logger.info(f"[{task.instance_id}] Cleaning up container...")
            sb.cleanup()
            result.duration = time.monotonic() - start

        return result

    def _run_mock_agent(self, task: Task) -> tuple:
        """Mock agent: returns the task's ground truth patch as a 'perfect agent'."""
        import time as _time
        _time.sleep(0.05)
        return task.patch, "", 0, 0.05

    # ── agent command construction ─────────────────────────────────

    def _build_agent_cmd(self, problem_statement: str) -> list[str]:
        """Build the agent command to run inside the container.

        The agent command is constructed from config. The repo is at /repo
        inside the container. The problem statement is passed via stdin.
        """
        agent_cfg = self.config.agent
        if agent_cfg.type == "opencode":
            return [
                agent_cfg.command,
                "solve",
                "/repo",
                problem_statement,
            ]
        # Generic: just run the configured command with the problem on stdin
        return [agent_cfg.command]

    # ── patch extraction ───────────────────────────────────────────

    @staticmethod
    def _extract_patch(stdout: str) -> str:
        """Extract unified diff from agent stdout."""
        import re
        # Check for markdown-fenced diff
        diff_re = re.compile(r"```diff\s*\n(.*?)```", re.DOTALL)
        m = diff_re.search(stdout)
        if m:
            return m.group(1).strip() + "\n"

        # Check if stdout already looks like a raw diff
        if stdout.strip().startswith("diff "):
            return stdout.strip() + "\n"

        # Try to find raw diff by looking for diff headers
        lines = stdout.splitlines()
        diff_lines: list[str] = []
        in_diff = False
        for line in lines:
            if line.startswith("diff ") or line.startswith("---") or line.startswith("+++"):
                in_diff = True
            if in_diff:
                diff_lines.append(line)

        if diff_lines:
            return "\n".join(diff_lines) + "\n"

        return stdout.strip() + "\n"
