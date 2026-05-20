# Configuration Reference

## Full Example

```yaml
agent:
  type: opencode           # Agent type (opencode | mock)
  install_cmd: ""          # Shell command to install the agent tool in the container
  version_cmd: ""          # Shell command to show installed version (runs after install_cmd)
  command: opencode        # CLI command; supports {problem_statement} template
  env: {}                  # Extra env vars passed to the container (e.g., API keys)
  timeout: 1800            # Agent timeout (seconds)
  # persist:               # Auto-mount container paths to host (optional)
  #   - /workspace
  #   - /root/.cache

sandbox:
  mode: auto               # auto | prebuilt
  repo_path: /repo         # Path inside container
  image: python:3.10-slim  # Docker image (supports {field} templates)
  setup_commands:          # Commands run inside container during init
    - "pip install -q opencode-cli"
  cleanup_image: false     # docker rmi after each task to save disk
  auto_pull_image: true    # auto-pull image if not present locally
  python_bin: python       # Python binary for running pytest (e.g., conda env)
  # mounts:                # Bind mounts (optional) — persist container paths to host
  #   - host_path: "workspace"   # relative → {output.dir}/{run_id}/{id}/mounts/workspace
  #     container_path: "/workspace"
  #     mode: rw

dataset:
  provider: local          # local | huggingface | url
  path: swe_verified.json  # File path, HF dataset ID, or URL
  type: swe_bench          # Dataset format
  split: test              # HF split name (huggingface only)
  name: null               # HF config/subset name (huggingface only)
  token: null              # HF API token (huggingface only)

execution:
  max_workers: 4           # Concurrent tasks
  timeout: 3600            # Per-task timeout (seconds)
  retries: 0               # Retry count on failure

output:
  dir: results             # Output directory
  log_level: INFO          # Log level: DEBUG | INFO | WARNING | ERROR
```

## Dataset Provider Examples

### local

```yaml
dataset:
  provider: local
  path: ./data/swe_verified.json
```

### huggingface

```yaml
dataset:
  provider: huggingface
  path: princeton-nlp/SWE-bench_Verified
  split: test
```

With private dataset:

```yaml
dataset:
  provider: huggingface
  path: org/private-dataset
  split: test
  token: hf_xxxxxxxxxxxx
```

### url

```yaml
dataset:
  provider: url
  path: https://example.com/dataset.json
```

## Sandbox Images

### Generic Python image (auto-install)

```yaml
sandbox:
  image: python:3.10-slim
  setup_commands:
    - "pip install -q pytest"
```

### Official SWE-bench pre-built image

```yaml
sandbox:
  mode: prebuilt
  repo_path: /testbed
  image: "swebench/sweb.eval.x86_64.{instance_id|split:__:0}_1776_{instance_id|split:__:1}"
  cleanup_image: false
```

Image template resolution uses task fields:

| Template | Value from `sympy__sympy-12481` |
|----------|-------------------------------|
| `{instance_id}` | `sympy__sympy-12481` |
| `{instance_id\|split:__:0}` | `sympy` |
| `{instance_id\|split:__:1}` | `sympy-12481` |
| `{repo}` | `sympy/sympy` |
| `{repo_owner}` | `sympy` (auto-derived) |
| `{repo_name}` | `sympy` (auto-derived) |
| `{version}` | `1.0` |

### Disk management

```yaml
sandbox:
  cleanup_image: true   # docker rmi after each task
```

Set `cleanup_image: true` on disk-constrained machines. Each SWE-bench image is ~2-5 GB; without cleanup they accumulate quickly with hundreds of tasks.

### Image pull behavior

```yaml
sandbox:
  auto_pull_image: true   # default: true
```

When `auto_pull_image: true` (the default), the harness checks if the resolved image exists locally via `docker image inspect`. If the image is missing, it runs `docker pull` automatically before creating the container.

Set `auto_pull_image: false` to disable automatic pulling — the harness will exit with an error if the image is not found.

### Docker availability check

The harness checks that the `docker` CLI is installed and the daemon is reachable before processing any tasks. If Docker is missing or the daemon is down, it exits immediately with a clear error message.

## Bind Mounts

Bind mounts persist files from inside the Docker container to the host filesystem. Use this to access agent-internal working files, cache directories, or any data the agent writes during execution.

### Configuration

```yaml
sandbox:
  mounts:
    - host_path: "mounts/{run_id}/{instance_id}/workspace"
      container_path: "/workspace"
      mode: rw
```

### Template Variables

`host_path` supports all template variables:

| Variable | Resolves to |
|----------|------------|
| `{run_id}` | Auto-generated timestamp or `--run-id` value |
| `{instance_id}` | Per-task instance identifier |
| `{repo_owner}` | Repository owner (auto-derived) |
| `{repo_name}` | Repository name (auto-derived) |
| `{version}` | Task version string |

All field templates (`{field}`, `{field|split:d:i}`) work in `host_path`.

Relative `host_path` values are resolved against `{output.dir}/{run_id}/{instance_id}/mounts`. Absolute paths (e.g., `/data/shared`) are used as-is.

### Recommended Structure

```
{output.dir}/
└── {run_id}/
    ├── results.json
    └── {instance_id}/
        ├── results/        (per-task logs, patch, result.json)
        └── mounts/         (bind mount host paths)
            ├── workspace/
            └── cache/
```

### Notes

- Host directories are created automatically if they don't exist.
- Bind mounts do not affect the evaluation logic — they only provide host visibility into container files.

### Agent persist (auto-mount shortcut)

A simpler alternative to `sandbox.mounts`: list container paths you want persisted, and the harness auto-generates host paths.

```yaml
agent:
  persist:
    - /workspace
    - /root/.cache
```

Host paths are auto-generated as:
```
{output.dir}/{run_id}/{instance_id}/mounts/{stripped_path}
```

For example, with `persist: [/workspace]` and instance `sympy__sympy-12481`:
- Host: `results/20260519_150900/sympy__sympy-12481/mounts/workspace`
- Container: `/workspace`

`persist` and `sandbox.mounts` can be used together — both are applied.

### Agent install command

Use `install_cmd` to install agent tools inside the container before evaluation. The command runs via `bash -c` after the sandbox is prepared.

```yaml
agent:
  type: opencode
  install_cmd: "npm install -g opencode-ai"
  command: "opencode run --auto -m deepseek/deepseek-v4-pro {problem_statement}"
```

### Agent command template

The `command` field supports a `{problem_statement}` template that gets replaced with the task's problem statement (shell-escaped). When the template is present, the command runs via `bash -c`; otherwise the bare command is invoked and the problem statement is passed on stdin.

```yaml
agent:
  command: "opencode run --auto -m deepseek/deepseek-v4-pro {problem_statement}"
```

Environment variables from `agent.env` are passed to the container via `docker exec -e`.

## CLI Arguments

```
python -m agautoeval <config.yaml> [options]

Options:
  --start N       Start at dataset index N (for slicing)
  --end N         End at dataset index N
  --instances ID  Run specific instances (comma-separated)
  --run-id ID     Run identifier for bind mount organization (default: auto-generated timestamp)
```

### Examples

```bash
# Run all tasks
python -m agautoeval configs/example.yaml

# Run first 10 tasks
python -m agautoeval configs/example.yaml --start 0 --end 10

# Run specific tasks
python -m agautoeval configs/example.yaml --instances "sympy__sympy-12481,django__django-12345"

# Run with a custom run ID for bind mount path organization
python -m agautoeval configs/example.yaml --run-id "experiment_42"
```
