# Evaluation Flow

## Per-Task Pipeline

Each task goes through 6 steps inside its own Docker container:

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: docker run -d --name agautoeval_{id} image          │
│         apt-get install git                                 │
│         pip install pytest                                  │
│         git clone <repo> /repo                              │
│         git checkout <base_commit>                          │
│         pip install -e /repo                                │
├─────────────────────────────────────────────────────────────┤
│ Step 2: docker exec agautoeval_{id} bash -c "<agent_cmd>"   │
│         agent modifies repo in-place; {problem_statement}    │
│         template resolved in command string                  │
├─────────────────────────────────────────────────────────────┤
│ Step 3: git add -A && git diff --cached HEAD                │
│         Capture all changes agent made to the repo           │
│         Then git reset --hard HEAD + git clean -fd           │
├─────────────────────────────────────────────────────────────┤
│ Step 4: docker exec agautoeval_{id} git apply - < patch     │
├─────────────────────────────────────────────────────────────┤
│ Step 5: docker exec agautoeval_{id} pytest -k test_name     │
│            for each FAIL_TO_PASS test                       │
│            for each PASS_TO_PASS test                       │
│         resolved = all(F2P) AND all(P2P)                    │
├─────────────────────────────────────────────────────────────┤
│ Step 6: docker stop agautoeval_{id}                         │
└─────────────────────────────────────────────────────────────┘
```

## SWE-bench Evaluation Protocol

SWE-bench does NOT compare patches textually. It runs tests.

| Test Type | Before Fix | After Fix | Purpose |
|-----------|------------|-----------|---------|
| FAIL_TO_PASS (F2P) | Fails | Must pass | Confirms bug is fixed |
| PASS_TO_PASS (P2P) | Passes | Must pass | Confirms no regressions |

**Resolution condition**: ALL F2P tests pass AND ALL P2P tests pass.

## Test Name Formats

SWE-bench test names come in two formats:

1. **Full path** (newer format):
   ```
   astropy/modeling/tests/test_separable.py::test_separable[compound_model6-result6]
   ```
   Run with: `pytest path/to/test.py::TestClass::test_name`

2. **Bare name** (older format):
   ```
   test_args
   ```
   Run with: `pytest -k test_name`

The `evaluate()` method detects the format by checking for `::` or `/` in the test spec.

## Error Handling

Each step can fail independently:

| Failure Point | TaskResult | Logged |
|--------------|------------|--------|
| Container creation fails | ERROR | sandbox log |
| Repo clone fails | ERROR | sandbox log |
| Agent exits non-zero | ERROR | agent_stderr.log |
| Agent produces empty patch | UNRESOLVED | (warning) |
| Patch fails to apply | UNRESOLVED | patch_error.log |
| F2P tests fail | UNRESOLVED (F2P: x/y) | f2p_failures.log |
| P2P tests fail | UNRESOLVED (P2P: x/y) | p2p_failures.log |
| All tests pass | RESOLVED | test_output.log |
| Unexpected exception | ERROR | error.log |

The `finally` block always runs `sb.cleanup()` — containers are destroyed even on failure.

## Concurrency Model

```
max_workers=1:
  Task 1 ──────────► Task 2 ──────────► Task 3

max_workers=4:
  Task 1 ──┐
  Task 2 ──┼── ThreadPoolExecutor(4)
  Task 3 ──┤
  Task 4 ──┘
  Task 5 ──► (waits for first slot)
```

Each task creates and destroys its own container. The container name includes the instance_id (`agautoeval_{instance_id}`), so two tasks can never collide.

## Output Structure

```
{output_dir}/
└── {run_id}/
    ├── results.json                         # Final scores + per-task details
    └── {instance_id}/
        ├── results/                         # Per-task logs and data
        │   ├── task_info.json               # Task metadata + image + problem
        │   ├── agent_cmd.json               # Agent mode: exact command executed
        │   ├── agent_stdout.log             # Agent raw stdout
        │   ├── agent_stderr.log             # Agent raw stderr
        │   ├── patch.diff                   # Extracted unified diff
        │   ├── result.json                  # Per-task result + timing
        │   ├── sandbox_clone.log
        │   ├── sandbox_checkout.log
        │   ├── sandbox_install_tools.log
        │   ├── sandbox_install_repo.log
        │   ├── test_output.log
        │   ├── f2p_failures.log             # Only if F2P failures exist
        │   ├── p2p_failures.log             # Only if P2P failures exist
        │   ├── patch_error.log              # Only if patch apply failed
        │   └── error.log                    # Only if exception occurred
        └── mounts/                          # Bind mount host paths
            └── ...                          # (from persist or sandbox.mounts)
```
