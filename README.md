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
python -m agautoeval configs/example.yaml --instances "sympy__sympy-12481"
```

Slice the dataset:

```bash
python -m agautoeval configs/example.yaml --start 0 --end 100
```

Custom run ID (for bind mount path organization):

```bash
python -m agautoeval configs/example.yaml --run-id "experiment_42"
```

## Config

```yaml
agent:
  type: opencode                                     # agent type (opencode | mock)
  install_cmd: "npm install -g opencode-ai"          # install command (runs in container)
  version_cmd: "opencode --version"                  # verify installed version
  command: "opencode run --auto -m model {problem_statement}"  # supports {problem_statement} template
  env:                                               # env vars passed to agent
    API_KEY: sk-xxx
  timeout: 1800
  persist:                                           # auto-mount container paths to host
    - /root/.local/share

sandbox:
  mode: prebuilt                                     # auto (clone+install) | prebuilt (SWE-bench images)
  repo_path: /testbed                                # /repo for auto, /testbed for prebuilt
  image: "swebench/sweb.eval.x86_64.{instance_id|split:__:0}_1776_{instance_id|split:__:1}"
  setup_commands:
    - "pip install -q pytest"
  cleanup_image: true                                # docker rmi after each task to save disk
  auto_pull_image: true                              # auto-pull image if not present locally
  # mounts:                                          # bind mounts (optional)
  #   - host_path: "workspace"
  #     container_path: "/workspace"
  #     mode: rw

dataset:
  provider: huggingface                              # local | huggingface | url
  path: SWE-bench/SWE-bench_Verified
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
```

Each task runs in its own Docker container for complete environment isolation.
See `CLAUDE.md` and `docs/` for the full architecture and configuration reference.
