# AgAutoEval

Automatic Agent Evaluation Harness — evaluate coding agents on SWE-bench Verified.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```bash
python -m agautoeval configs/example.yaml
```

Filter specific instances:

```bash
python -m agautoeval config.yaml --instances "sympy__sympy-12481,django__django-12345"
```

Slice the dataset:

```bash
python -m agautoeval config.yaml --start 0 --end 100
```

## Config

```yaml
agent:
  type: opencode
  command: opencode
  timeout: 1800

sandbox:
  image: swebench/sweb.eval.x86_64.sympy_1776_sympy-12481
  setup_commands: []

dataset:
  provider: local          # local | huggingface | url
  path: swe_verified.json
  type: swe_bench

execution:
  max_workers: 4
  timeout: 3600
  retries: 0

output:
  dir: results
  log_level: INFO
```

### Dataset providers

| Provider | Example |
|----------|---------|
| `local` | `path: swe_verified.json` |
| `huggingface` | `path: princeton-nlp/SWE-bench_Verified`, `split: test` |
| `url` | `path: https://example.com/dataset.json` |

## Architecture

```
config.yaml → dataset → [Docker container per task] → agent → patch → F2P/P2P tests → score
```

Each task runs in its own Docker container for complete environment isolation.
