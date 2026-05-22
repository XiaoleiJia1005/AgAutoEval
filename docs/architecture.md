# Architecture

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        agautoeval                           │
│                                                             │
│  config.yaml ─► __main__.py ─► Executor.run()               │
│                                    │                        │
│                    ┌───────────────┼───────────────┐        │
│                    │               │               │        │
│               dataset.py     executor.py     sandbox.py     │
│               (load tasks)   (orchestrate)  (Docker per    │
│                    │               │          task)         │
│                    │               ▼                        │
│                    │     ┌── _run_one() ──┐                │
│                    │     │  1. prepare    │                │
│                    │     │  2. run agent  │                │
│                    │     │  3. extract    │                │
│                    │     │  4. apply      │                │
│                    │     │  5. evaluate   │                │
│                    │     │  6. cleanup    │                │
│                    │     └────────────────┘                │
│                    │               │                        │
│               logger.py ◄─────────┘                        │
│               scorer.py                                     │
│               reporter.py ─► console + {run_dir}/results.json
└──────────────────────────────────────────────────────────────┘
```

## Package Structure

```
agautoeval/
├── __init__.py           # Package version
├── __main__.py           # CLI entry point
├── config.py             # YAML → pydantic models
├── dataset.py            # Multi-provider task loader
├── executor.py           # Core evaluation pipeline
├── sandbox.py            # Per-task Docker container
├── logger.py             # Structured per-task logging
├── scorer.py             # Score computation
├── reporter.py           # Console + JSON output
└── agent/
    ├── __init__.py       # Agent registry + factory
    ├── base.py           # Abstract BaseAgent
    ├── opencode.py       # OpenCode CLI adapter
    └── mock.py           # Mock agent for testing
```

## Data Flow

```
YAML config
  │
  ▼
DatasetConfig ─► load_dataset() ─► list[Task]
  │                                    │
  │                              Executor.run()
  │                                    │
  │                        ┌───────────┴───────────┐
  │                        │   ThreadPoolExecutor  │
  │                        │                       │
  │                        │  _run_one(task):      │
  │                        │    DockerSandbox       │
  │                        │    .prepare(task)     │
  │                        │    .run_agent_command │
  │                        │    .apply_patch()     │
  │                        │    .evaluate(f2p,p2p) │
  │                        │    .cleanup()         │
  │                        │                       │
  │                        │  ─► TaskResult        │
  │                        └───────────────────────┘
  │                                    │
  ▼                                    ▼
compute_score() ◄── [TaskResult, ...]
  │
  ▼
print_summary()  ─►  console table
write_json()     ─►  {run_dir}/results.json
```

## Isolation Model

Each task runs in its own Docker container:

```
Task A ─► container_agautoeval_A ─► destroyed
Task B ─► container_agautoeval_B ─► destroyed
Task C ─► container_agautoeval_C ─► destroyed
```

- **Repo**: cloned inside container at `/repo`
- **Agent**: executes inside container via `docker exec`
- **Dependencies**: installed inside container (isolated from host)
- **Tests**: run inside container via `docker exec`
- **Cleanup**: container stopped and removed after each task
