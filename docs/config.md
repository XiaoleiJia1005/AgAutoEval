# Configuration Reference

## Full Example

```yaml
agent:
  type: opencode           # Agent type (opencode | mock)
  command: opencode        # CLI command
  env: {}                  # Extra env vars
  timeout: 1800            # Agent timeout (seconds)

sandbox:
  mode: auto               # auto | prebuilt
  repo_path: /repo         # Path inside container
  image: python:3.10-slim  # Docker image (supports {field} templates)
  setup_commands:          # Commands run inside container during init
    - "pip install -q opencode-cli"
  cleanup_image: false     # docker rmi after each task to save disk

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

## CLI Arguments

```
python -m agautoeval <config.yaml> [options]

Options:
  --start N       Start at dataset index N (for slicing)
  --end N         End at dataset index N
  --instances ID  Run specific instances (comma-separated)
```

### Examples

```bash
# Run all tasks
python -m agautoeval configs/example.yaml

# Run first 10 tasks
python -m agautoeval configs/example.yaml --start 0 --end 10

# Run specific tasks
python -m agautoeval configs/example.yaml --instances "sympy__sympy-12481,django__django-12345"
```
