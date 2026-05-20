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
from agautoeval.sandbox import DockerSandbox, check_docker


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

    def __init__(self, config: Config, logger: TaskLogger, run_id: str | None = None):
        self.config = config
        self.logger = logger
        self.run_id = run_id or self._default_run_id()
        self.output_dir = (Path(config.output.dir) / self.run_id).resolve()

    @staticmethod
    def _default_run_id() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def run(self, tasks: list[Task]) -> list[TaskResult]:
        # Fail fast if Docker is not available
        check_docker()

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
        timing: dict[str, float] = {}

        # Resolve per-task image template
        task_fields = task.model_dump()
        task_fields["repo_owner"] = task.repo.split("/")[0] if "/" in task.repo else task.repo
        task_fields["repo_name"] = task.repo.split("/")[1] if "/" in task.repo else task.repo
        image = self.config.sandbox.resolve_image(task_fields)
        setup_cmds = self.config.sandbox.resolve_setup_commands(task_fields)

        # Resolve bind mounts (relative paths resolve against task mount dir)
        mount_base = str(self.output_dir / task.instance_id / "mounts")
        mount_specs = self.config.sandbox.resolve_mounts(
            task_fields, self.run_id, base_dir=mount_base,
        )
        mount_tuples = [(m.host_path, m.container_path, m.mode) for m in mount_specs]

        # Auto-generate mounts from agent.persist paths
        for cp in self.config.agent.persist:
            host_path = str(Path(mount_base) / cp.lstrip("/"))
            mount_tuples.append((host_path, cp, "rw"))

        # ── Save task metadata ─────────────────────────────────
        self.logger.write_task_json(task.instance_id, "task_info.json", {
            "instance_id": task.instance_id,
            "repo": task.repo,
            "base_commit": task.base_commit,
            "version": task.version,
            "image": image,
            "mode": self.config.sandbox.mode,
            "agent_type": self.config.agent.type,
            "f2p_count": len(task.fail_to_pass),
            "p2p_count": len(task.pass_to_pass),
            "problem_statement": task.problem_statement,
        })

        sb = DockerSandbox(
            image=image,
            timeout=self.config.execution.timeout,
            mode=self.config.sandbox.mode,
            repo_path=self.config.sandbox.repo_path,
            setup_commands=setup_cmds,
            cleanup_image=self.config.sandbox.cleanup_image,
            auto_pull_image=self.config.sandbox.auto_pull_image,
            mounts=mount_tuples,
        )

        try:
            # ── Step 1: Create container and prepare repo ──────────
            self.logger.info(f"[{task.instance_id}] Starting Docker container...")
            for host_path, container_path, mode in mount_tuples:
                self.logger.info(
                    f"[{task.instance_id}] Mount: {host_path} "
                    f"-> {container_path} ({mode})"
                )
            t0 = time.monotonic()
            prep = sb.prepare(task)
            timing["prepare"] = time.monotonic() - t0
            result.sandbox_logs = prep.logs

            for name, content in prep.logs.items():
                self.logger.write_task_log(
                    task.instance_id, f"sandbox_{name}.log", content
                )

            if not prep.passed:
                result.error = prep.error
                self.logger.error(f"[{task.instance_id}] Sandbox failed: {prep.error}")
                result.duration = time.monotonic() - start
                self._save_result(task.instance_id, result, timing)
                return result

            # ── Install agent tool if configured ───────────────────
            if self.config.agent.install_cmd:
                cmd = self.config.agent.install_cmd
                if "npm" in cmd:
                    sb.ensure_npm()
                self.logger.info(
                    f"[{task.instance_id}] Installing agent: {cmd}"
                )
                out, err, rc = sb.exec(
                    ["bash", "-c", cmd],
                    cwd="/",
                    timeout=600,
                )
                if out:
                    self.logger.info(f"[{task.instance_id}] install: {out.strip()}")
                if err:
                    self.logger.warning(f"[{task.instance_id}] install stderr: {err.strip()}")
                if rc != 0:
                    self.logger.warning(
                        f"[{task.instance_id}] install_cmd exited with code {rc}"
                    )

            # ── Show agent version if configured ────────────────────
            if self.config.agent.version_cmd:
                cmd = self.config.agent.version_cmd
                self.logger.info(
                    f"[{task.instance_id}] Agent version: {cmd}"
                )
                out, err, rc = sb.exec(
                    ["bash", "-c", cmd],
                    cwd="/",
                    timeout=30,
                )
                if out.strip():
                    self.logger.info(f"[{task.instance_id}] {out.strip()}")
                if err:
                    self.logger.warning(f"[{task.instance_id}] version stderr: {err.strip()}")
                if rc != 0:
                    self.logger.warning(
                        f"[{task.instance_id}] version_cmd exited with code {rc}"
                    )

            # ── Step 2: Run agent inside container ─────────────────
            self.logger.info(f"[{task.instance_id}] Running agent in container...")
            t0 = time.monotonic()
            is_mock = self.config.agent.type == "mock"
            if is_mock:
                agent_stdout, agent_stderr, agent_rc, agent_dur = \
                    self._run_mock_agent(task)
            else:
                agent_cmd = self._build_agent_cmd(task.problem_statement)
                # Save the exact command used
                self.logger.write_task_json(task.instance_id, "agent_cmd.json", {
                    "command": agent_cmd,
                    "timeout": self.config.agent.timeout,
                })
                agent_stdout, agent_stderr, agent_rc, agent_dur = sb.run_agent_command(
                    agent_cmd,
                    task.problem_statement,
                    timeout=self.config.agent.timeout,
                    env=self.config.agent.env,
                )
            timing["agent"] = time.monotonic() - t0
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
                self._save_result(task.instance_id, result, timing)
                return result

            # ── Step 3: Extract patch ──────────────────────────────
            if is_mock:
                # Mock agent returns the ground-truth patch directly
                patch = agent_stdout
            else:
                # Agent modifies the repo; capture all changes via git diff
                repo = self.config.sandbox.repo_path
                sb.exec(["git", "add", "-A"], cwd=repo)
                diff_out, _, _ = sb.exec(["git", "diff", "--cached", "HEAD"], cwd=repo)
                # Reset working tree to HEAD so patch can be applied cleanly
                sb.exec(["git", "reset", "--hard", "HEAD"], cwd=repo)
                sb.exec(["git", "clean", "-fd"], cwd=repo)
                patch = diff_out
            self.logger.write_task_log(task.instance_id, "patch.diff", patch)

            if not patch.strip():
                result.error = "Agent produced no changes"
                self.logger.warning(f"[{task.instance_id}] Empty patch")
                result.duration = time.monotonic() - start
                self._save_result(task.instance_id, result, timing)
                return result

            # ── Step 4: Apply patch inside container ───────────────
            self.logger.info(f"[{task.instance_id}] Applying patch...")
            t0 = time.monotonic()
            patch_res = sb.apply_patch(patch)
            timing["apply_patch"] = time.monotonic() - t0
            if not patch_res.passed:
                result.error = patch_res.error
                self.logger.write_task_log(
                    task.instance_id, "patch_error.log", patch_res.error
                )
                result.duration = time.monotonic() - start
                self._save_result(task.instance_id, result, timing)
                return result

            # ── Step 5: Evaluate (SWE-bench protocol) ────────────
            self.logger.info(
                f"[{task.instance_id}] Running evaluation "
                f"(F2P={len(task.fail_to_pass)}, P2P={len(task.pass_to_pass)})..."
            )
            t0 = time.monotonic()
            test_res = sb.evaluate(task.fail_to_pass, task.pass_to_pass)
            timing["evaluate"] = time.monotonic() - t0
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
            t0 = time.monotonic()
            self.logger.info(f"[{task.instance_id}] Cleaning up container...")
            sb.cleanup()
            timing["cleanup"] = time.monotonic() - t0
            result.duration = time.monotonic() - start
            self._save_result(task.instance_id, result, timing)

        return result

    def _save_result(
        self, instance_id: str, result: TaskResult, timing: dict[str, float]
    ) -> None:
        """Save per-task result and timing as JSON."""
        self.logger.write_task_json(instance_id, "result.json", {
            "instance_id": result.instance_id,
            "resolved": result.resolved,
            "error": result.error,
            "duration": result.duration,
            "agent_duration": result.agent_duration,
            "f2p": f"{result.f2p_passed}/{result.f2p_total}" if result.f2p_total else None,
            "p2p": f"{result.p2p_passed}/{result.p2p_total}" if result.p2p_total else None,
            "timing": timing,
        })

    def _run_mock_agent(self, task: Task) -> tuple:
        """Mock agent: returns the task's ground truth patch as a 'perfect agent'."""
        import time as _time
        _time.sleep(0.05)
        return task.patch, "", 0, 0.05

    # ── agent command construction ─────────────────────────────────

    def _build_agent_cmd(self, problem_statement: str) -> list[str]:
        """Build the agent command to run inside the container.

        If the command contains {problem_statement}, it is resolved and the
        full command runs via bash -c. Otherwise the bare command is returned
        and the problem statement is passed on stdin.
        """
        import shlex
        agent_cfg = self.config.agent
        cmd_str = agent_cfg.command

        if "{problem_statement}" in cmd_str:
            resolved = cmd_str.replace(
                "{problem_statement}", shlex.quote(problem_statement),
            )
            return ["bash", "-c", resolved]

        return [agent_cfg.command]

