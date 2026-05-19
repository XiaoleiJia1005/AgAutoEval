"""CLI entry point: python -m agautoeval <config.yaml>"""

import argparse
import sys
from pathlib import Path

from agautoeval.config import load_config
from agautoeval.dataset import Task, load_dataset, slice_dataset
from agautoeval.executor import Executor
from agautoeval.logger import TaskLogger
from agautoeval.reporter import print_summary, write_json
from agautoeval.scorer import compute_score


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
        help="Comma-separated list of specific instance IDs to run",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run identifier for bind mount path organization (default: auto-generated timestamp)",
    )
    args = parser.parse_args(argv)

    # Load config
    print(f"Loading config: {args.config}")
    config = load_config(args.config)

    # Determine run ID and create run directory
    from datetime import datetime
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (Path(config.output.dir) / run_id).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    # Setup logger
    logger = TaskLogger(run_dir, config.output.log_level)
    logger.info(f"Run directory: {run_dir}")
    logger.info(f"Run ID: {run_id}")

    # Load dataset
    logger.info(
        f"Loading dataset [provider={config.dataset.provider}]: "
        f"{config.dataset.path}"
    )
    tasks = load_dataset(config.dataset)
    logger.info(f"Loaded {len(tasks)} tasks")

    # Filter by instance IDs or slice
    if args.instances:
        wanted = set(args.instances.split(","))
        tasks = [t for t in tasks if t.instance_id in wanted]
        logger.info(f"Filtered to {len(tasks)} tasks by --instances")
    else:
        tasks = slice_dataset(tasks, args.start, args.end)

    if not tasks:
        logger.error("No tasks to evaluate. Check dataset path and filters.")
        sys.exit(1)

    # Run evaluation
    executor = Executor(config, logger, run_id=run_id)
    results = executor.run(tasks)

    # Score and report
    report = compute_score(results)
    print_summary(report, results)
    write_json(report, results, run_dir / "results.json")


if __name__ == "__main__":
    main()
