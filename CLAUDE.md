# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode
pip install -e .

# Run evaluation (results go to ~/.agautoeval/<run_id>/ by default)
python -m agautoeval configs/example_opencode.yaml

# Custom output directory
python -m agautoeval config.yaml --output-dir /data/results

# Filter by instance IDs
python -m agautoeval config.yaml --instances "sympy__sympy-12481,django__django-12345"

# Slice the dataset
python -m agautoeval config.yaml --start 0 --end 100
```

No test suite or linter is configured in this repo.

## Output structure

Results go to `<output.dir>/<run_id>/` (default: `~/.agautoeval/<run_id>/`):

```
~/.agautoeval/
  20260521_193000/               # run_id
    config.yaml                  # copy of the config used for this run
    results.json                 # overall evaluation summary
    <instance_id>/               # per-task
      results/                   # logs, patches, evaluation output
        task_info.json
        patch.diff
        agent_stdout.log
        test_output.log
        ...
      mounts/                    # auto-mounts from agent.persist
```

## Architecture

AgAutoEval evaluates coding agents on SWE-bench Verified. Each task gets its own Docker container for complete environment isolation. The 6-step per-task pipeline is:

1. **Prepare** — create container, install git/pytest, clone repo at commit, `pip install -e`, run `agent.install_cmd` if configured
2. **Run agent** — execute agent via `docker exec` with `agent.env` vars; command supports `{problem_statement}` template
3. **Extract patch** — `git add -A && git diff --cached HEAD` inside container, then reset to HEAD for clean apply
4. **Apply patch** — `git apply` inside container
5. **Evaluate** — run F2P (must now pass) and P2P (must still pass) tests; resolved = all pass
6. **Cleanup** — `docker stop` container (auto-removed via `--rm`)

Key design decisions:

- **Agent abstraction**: `agent/` defines `BaseAgent` (abstract) with a clear interface for building Docker commands, managing install/version steps, and ensuring runtime dependencies. The executor creates agents via the `create_agent()` factory and delegates all agent-specific behavior to the agent instance — it does not know which concrete agent type it is running. Adding a new agent means subclassing `BaseAgent`, implementing `build_command()`, and registering it in `_AGENT_REGISTRY`.

  Key agent interface methods:
  - `build_command(problem_statement)` — returns the `docker exec` command list
  - `get_install_cmd()` / `get_version_cmd()` — tool installation and verification
  - `ensure_runtime(sandbox)` / `post_install(sandbox)` — pre/post install hooks
  - `get_env()` — environment variables for the agent process
  - `is_mock` property — whether the agent is a mock (returns ground-truth patch)

- **Mock agent** (`agent.type: mock`) uses the task's ground-truth patch to verify the pipeline itself. The executor checks `agent.is_mock` to decide whether to run the agent or return the ground-truth patch directly.
- **Sandbox modes**: `auto` (clone repo, install deps from scratch) vs `prebuilt` (official SWE-bench images with everything already set up at `/testbed`).
- **Image templates**: sandbox image strings support `{field}` and `{field|split:d:i}` syntax for per-task image resolution.
- **Dataset providers**: `local` (JSON file), `huggingface` (HF Hub via `datasets` library or API fallback), `url` (HTTP fetch). HF stores F2P/P2P as JSON strings that get auto-parsed into lists.
- **Concurrency**: `ThreadPoolExecutor` for parallel task execution; each task gets its own Docker container named `agautoeval_{instance_id}` to prevent collisions.
- **Task dataset format** (`dataset.py:Task`): pydantic model with `instance_id`, `repo`, `base_commit`, `problem_statement`, `patch` (ground truth), `test_patch`, `fail_to_pass`, `pass_to_pass`.

## Configuration

See `docs/config.md` for the full config reference. Notable sandbox fields beyond the basics:

| Field | Purpose |
|-------|---------|
| `sandbox.mode` | `auto` (clone + install) or `prebuilt` (SWE-bench official images) |
| `sandbox.repo_path` | Path inside container (`/repo` for auto, `/testbed` for prebuilt) |
| `sandbox.cleanup_image` | `docker rmi` after each task to save disk on constrained machines |
| `sandbox.auto_pull_image` | Auto-pull image if not present locally (default: true) |
| `sandbox.image` | Supports `{instance_id}`, `{instance_id|split:__:0}`, `{repo}`, etc. |
