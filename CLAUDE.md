# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode
pip install -e .

# Run evaluation
python -m agautoeval configs/example.yaml

# Filter by instance IDs
python -m agautoeval config.yaml --instances "sympy__sympy-12481,django__django-12345"

# Slice the dataset
python -m agautoeval config.yaml --start 0 --end 100
```

No test suite or linter is configured in this repo.

## Architecture

AgAutoEval evaluates coding agents on SWE-bench Verified. Each task gets its own Docker container for complete environment isolation. The 6-step per-task pipeline is:

1. **Prepare** — create container, install git/pytest, clone repo at commit, `pip install -e`
2. **Run agent** — execute agent inside container via `docker exec`, pipe problem statement on stdin
3. **Extract patch** — parse `` ```diff `` fences or raw diff headers from agent stdout
4. **Apply patch** — `git apply` inside container
5. **Evaluate** — run F2P (must now pass) and P2P (must still pass) tests; resolved = all pass
6. **Cleanup** — `docker stop` container (auto-removed via `--rm`)

Key design decisions:

- **Agent abstraction**: `agent/` defines `BaseAgent` (abstract) + registry in `__init__.py`. Adding a new agent means subclassing `BaseAgent`, implementing `run()`, and registering it in `_AGENT_REGISTRY`. Agents can be used in two modes:
  - **Standalone mode** (legacy): `BaseAgent.run()` is called on the host — useful for testing agents without Docker
  - **Container mode** (primary): The executor builds a shell command from config and runs it inside the Docker sandbox via `sb.run_agent_command()`. This is the main path — it sidesteps the agent abstraction at runtime.
- **Mock agent** (`agent.type: mock`) uses the task's ground-truth patch to verify the pipeline itself.
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
| `sandbox.image` | Supports `{instance_id}`, `{instance_id|split:__:0}`, `{repo}`, etc. |
