"""CLI entry point: python -m agautoeval <config.yaml>"""

import argparse
import fnmatch
import shutil
import sys
from pathlib import Path

from agautoeval.config import load_config
from agautoeval.dataset import Task, load_dataset, slice_dataset
from agautoeval.executor import Executor
from agautoeval.logger import TaskLogger
from agautoeval.reporter import print_summary, write_json
from agautoeval.scorer import compute_score


def _resolve_dir(raw: str) -> Path:
    """Resolve a directory path, expanding ~ to the user home."""
    return Path(raw).expanduser().resolve()


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="agautoeval",
        description="Automatic Agent Evaluation Harness",
    )
    parser.add_argument(
        "config",
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start index for dataset slicing",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End index for dataset slicing",
    )
    parser.add_argument(
        "--instances",
        type=str,
        default=None,
        help="Comma-separated instance IDs or glob patterns (e.g., 'sympy*')",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma-separated instance ID patterns to exclude (e.g., 'django*')",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Filter by repo name pattern (e.g., 'sympy*', 'django/*')",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run identifier (default: auto-generated timestamp)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override the output base directory (default: ~/.agautoeval)",
    )
    args = parser.parse_args(argv)

    # Load config
    print(f"Loading config: {args.config}")
    config = load_config(args.config)

    # Resolve output directory (CLI flag overrides config default)
    output_base = _resolve_dir(args.output_dir or config.output.dir)
    config.output.dir = str(output_base)  # push resolved path back to config

    # Determine run ID and create run directory
    from datetime import datetime
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_base / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save a copy of the config YAML for reproducibility
    config_dest = run_dir / "config.yaml"
    shutil.copy2(args.config, config_dest)

    # Setup logger
    logger = TaskLogger(run_dir, config.output.log_level)
    logger.info(f"Run directory: {run_dir}")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Config saved to: {config_dest}")

    # Load dataset
    logger.info(
        f"Loading dataset [provider={config.dataset.provider}]: "
        f"{config.dataset.path}"
    )
    tasks = load_dataset(config.dataset)
    logger.info(f"Loaded {len(tasks)} tasks")

    # Filter by repo pattern
    if args.repo:
        tasks = [t for t in tasks if fnmatch.fnmatch(t.repo, args.repo)]
        logger.info(f"Filtered to {len(tasks)} tasks by --repo '{args.repo}'")

    # Filter by instance ID patterns (supports glob wildcards)
    if args.instances:
        patterns = [p.strip() for p in args.instances.split(",")]
        tasks = [
            t for t in tasks
            if any(fnmatch.fnmatch(t.instance_id, p) for p in patterns)
        ]
        logger.info(f"Filtered to {len(tasks)} tasks by --instances")

    # Exclude by instance ID patterns
    if args.exclude:
        patterns = [p.strip() for p in args.exclude.split(",")]
        tasks = [
            t for t in tasks
            if not any(fnmatch.fnmatch(t.instance_id, p) for p in patterns)
        ]
        logger.info(f"Filtered to {len(tasks)} tasks by --exclude")

    # Slice by index
    if not args.instances or args.start > 0 or args.end is not None:
        tasks = slice_dataset(tasks, args.start, args.end)

    if not tasks:
        logger.error("No tasks to evaluate. Check dataset path and filters.")
        sys.exit(1)

    # Run evaluation
    executor = Executor(config, logger, run_id=run_id)
    results = executor.run(tasks)

    # Score and report
    metadata = {
        "agent_type": config.agent.type,
        "model": config.agent.resolve_model(),
        "provider": config.agent.resolve_provider(),
        "dataset_path": config.dataset.path,
        "dataset_provider": config.dataset.provider,
        "dataset_type": config.dataset.type,
        "run_id": run_id,
        # Agent version tracking
        "agent_version": config.agent.version,
        "agent_commit": config.agent.commit,
        "agent_prompt_version": config.agent.prompt_version,
        "agent_tool_policy": config.agent.tool_policy,
    }
    report = compute_score(results, metadata=metadata)
    print_summary(report, results)
    write_json(report, results, run_dir / "results.json")


if __name__ == "__main__":
    main()
