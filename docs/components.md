# Components

## config.py — Configuration

Loads and validates YAML config via pydantic.

| Model | Key Fields | Purpose |
|-------|-----------|---------|
| `AgentConfig` | `type`, `command`, `env`, `timeout`, `persist` | Agent identity, invocation, and auto-mount paths |
| `SandboxConfig` | `image`, `setup_commands` | Docker image + container init |
| `DatasetConfig` | `path`, `provider`, `split`, `name`, `token` | Dataset source |
| `ExecutionConfig` | `max_workers`, `timeout`, `retries` | Concurrency + limits |
| `OutputConfig` | `dir`, `log_level` | Output paths + log verbosity |

Entry: `load_config(path) -> Config`

## dataset.py — Dataset Loader

Loads evaluation tasks with provider dispatch.

| Provider | Source | Implementation |
|----------|--------|---------------|
| `local` | JSON file | `json.load(open(path))` |
| `huggingface` | HF Hub | `datasets.load_dataset()` with F2P/P2P JSON string parsing |
| `url` | HTTP endpoint | `urllib.request` + `json.load()` |

Key: `Task` pydantic model with `instance_id`, `repo`, `base_commit`, `problem_statement`, `patch`, `test_patch`, `fail_to_pass`, `pass_to_pass`.

Note: HuggingFace stores F2P/P2P as JSON strings — the loader auto-parses them into lists.

## sandbox.py — Docker Sandbox

Per-task Docker container with full isolation.

```python
class DockerSandbox:
    # Lifecycle
    prepare(task)          # Create container, install git+pytest, clone repo
    cleanup()              # docker stop container

    # Execution
    exec(cmd, cwd, stdin)  # Run command inside container via docker exec
    exec_check(cmd, ...)   # Run + raise on non-zero

    # Pipeline steps
    run_agent_command()    # Execute agent inside container
    apply_patch(patch)     # git apply inside container
    evaluate(f2p, p2p)     # SWE-bench F2P/P2P protocol
```

**Repo preparation**:
- `file://` or `/` paths: clone on host, `docker cp` into container
- `http(s)://` paths: clone directly inside container
- After clone: `pip install -e /repo` inside container

**Evaluation protocol** (`evaluate`):
1. Run each FAIL_TO_PASS test with `pytest -k <name>` (bare names) or `pytest <full_path>` (paths with `::`)
2. Run each PASS_TO_PASS test same way
3. `resolved` = all F2P pass AND all P2P pass

## executor.py — Pipeline Orchestrator

Concurrent task execution with ThreadPoolExecutor.

```python
class Executor:
    def run(tasks) -> list[TaskResult]:
        # max_workers <= 1: sequential with tqdm
        # max_workers > 1:  ThreadPoolExecutor + tqdm

    def _run_one(task) -> TaskResult:
        1. sb.prepare(task)                 # Create container
        2. sb.run_agent_command(...)        # Run agent (or mock)
        3. _extract_patch(agent_stdout)     # Parse diff
        4. sb.apply_patch(patch)            # Apply
        5. sb.evaluate(f2p, p2p)            # Test
        6. sb.cleanup()                     # Destroy
```

Mock agent (`agent.type: mock`): uses task's ground truth `patch` field — useful for pipeline verification and baseline testing.

Patch extraction handles:
- ` ```diff ... ``` ` markdown fences
- Raw `diff --git` headers
- Fallback: entire stdout

## agent/ — Agent Abstraction

```
BaseAgent (abstract)
  ├── OpenCodeAgent    (opencode solve <repo> "<problem>")
  ├── MockAgent        (returns hardcoded patch, for testing)
  └── (extensible)     (subclass BaseAgent, register in __init__.py)
```

**Agent registry** in `agent/__init__.py`:
```python
_AGENT_REGISTRY = {"opencode": OpenCodeAgent, "mock": MockAgent}
create_agent("opencode", command="...", timeout=...) -> BaseAgent
```

## logger.py — Structured Logging

`TaskLogger` provides dual output:
- **Console**: real-time progress via Python `logging`
- **Files**: `{output_dir}/{instance_id}/results/` with separate files per log category

Log files per task:
| File | Content |
|------|---------|
| `task_info.json` | Task metadata (repo, commit, image, problem_statement) |
| `agent_cmd.json` | Exact agent command executed |
| `agent_stdout.log` | Agent stdout (raw output) |
| `agent_stderr.log` | Agent stderr |
| `patch.diff` | Extracted unified diff patch |
| `sandbox_clone.log` | Git clone output |
| `sandbox_checkout.log` | Commit checkout |
| `sandbox_install_tools.log` | apt-get / pip install |
| `sandbox_install_repo.log` | pip install -e /repo |
| `patch_error.log` | git apply failure detail |
| `test_output.log` | F2P/P2P evaluation summary |
| `f2p_failures.log` | Failed F2P tests |
| `p2p_failures.log` | Failed P2P tests |
| `result.json` | Per-task result (resolved, timing, scores) |
| `error.log` | Unexpected exceptions |

## scorer.py — Scoring

```python
compute_score(results) -> ScoreReport:
    total, resolved, failed, accuracy
    total_duration, avg_duration
    error_count
```

## reporter.py — Output

- `print_summary()`: console table with instance_id, result (RESOLVED/FAIL/ERROR), F2P (x/y), P2P (x/y), time
- `write_json()`: `results.json` with summary + per-task details
