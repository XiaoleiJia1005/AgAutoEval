# AgAutoEval

Automatic Agent Evaluation Harness — evaluate coding agents on SWE-bench Verified.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Run evaluation (results → ~/.agautoeval/<run_id>/)
python -m agautoeval configs/example_opencode.yaml

# Custom output directory
python -m agautoeval configs/example_opencode.yaml --output-dir /data/results

# Filter by instance IDs
python -m agautoeval configs/example_opencode.yaml --instances "sympy__sympy-12481,django__django-12345"

# Slice the dataset
python -m agautoeval configs/example_opencode.yaml --start 0 --end 100

# Custom run ID
python -m agautoeval configs/example_opencode.yaml --run-id "experiment_42"
```

## UI — Browse Results

Start the API server and frontend to browse evaluation results:

```bash
# Terminal 1: FastAPI server (port 8520)
python -m agautoeval.ui.server --dev

# Terminal 2: Vue.js frontend (port 5173, proxies to :8520)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** — three pages:
- **Runs** — table of all runs with agent, provider, model, accuracy, F2P
- **Run Detail** — per-run summary cards + instance results table
- **Instance** — chat-style agent messages, patch diff, raw logs

UI reads from `~/.agautoeval/` by default (the same directory the harness writes to).

## Config

See `configs/` for complete examples. Key fields:

```yaml
agent:
  type: opencode                       # agent type: opencode | claude | swe_agent | mock
  model: deepseek-v4-pro              # model name (auto-detected from -m in command if omitted)
  provider: deepseek                  # provider (auto-detected from model or command)
  install_cmd: "npm install -g opencode-ai"
  version_cmd: "opencode --version"
  command: "opencode run -m {provider}/{model} {problem_statement}"  # {provider}, {model}, {problem_statement} are resolved
  env:
    DEEPSEEK_API_KEY: sk-xxx
  timeout: 1800
  persist:                            # auto-mount container paths → host
    - /root/.local/share/

sandbox:
  mode: prebuilt                      # auto (clone+install) | prebuilt (SWE-bench images)
  repo_path: /testbed
  image: "swebench/sweb.eval.x86_64.{instance_id|split:__:0}_1776_{instance_id|split:__:1}"
  setup_commands:
    - "pip install -q pytest"
  cleanup_image: true                 # docker rmi after each task to save disk

dataset:
  provider: huggingface               # local | huggingface | url
  path: SWE-bench/SWE-bench_Verified
  type: swe_bench

execution:
  max_workers: 4
  timeout: 3600
  retries: 0
```

### Command templates

The `command` field supports `{problem_statement}`, `{model}`, and `{provider}`:

```yaml
# OpenCode / mini-swe-agent
command: "opencode run -m {provider}/{model} {problem_statement}"
command: "mini -m {provider}/{model} -t {problem_statement} -y"

# Claude Code (model via API key, no -m flag)
command: "claude -p {problem_statement}"
```

### Dataset providers

| Provider | Example |
|----------|---------|
| `local` | `path: swe_verified.json` |
| `huggingface` | `path: SWE-bench/SWE-bench_Verified`, `split: test` |
| `url` | `path: https://example.com/dataset.json` |

## Architecture

```
config.yaml → dataset → [Docker container per task]
  ├─ prepare (clone/checkout, install deps, install_cmd if configured)
  ├─ run agent (modifies repo in-place)
  ├─ git diff → patch
  ├─ git apply patch → F2P/P2P tests
  └─ cleanup

~/.agautoeval/<run_id>/                        # results written by harness
  ├─ config.yaml                               #   config snapshot
  ├─ results.json                              #   aggregate scores + metadata
  └─ <instance_id>/results/                    #   per-instance logs, patches, test output

agautoeval/ui/server.py     # FastAPI backend  — reads ~/.agautoeval/    (:8520)
frontend/                   # Vue 3 + Vite    — browse runs & messages  (:5173)
```

Each task runs in its own Docker container for complete environment isolation.
See `CLAUDE.md` and `docs/` for the full architecture and configuration reference.
