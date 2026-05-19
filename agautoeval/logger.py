"""Structured logging infrastructure.

Creates per-task log directories and provides both file and console logging.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path


class TaskLogger:
    """Logger that writes to both console and per-task log files."""

    def __init__(self, output_dir: Path, log_level: str = "INFO"):
        self.output_dir = Path(output_dir)
        self.log_level = log_level.upper()
        self._start_time = datetime.now(timezone.utc)

        self._root_logger = logging.getLogger("agautoeval")
        self._root_logger.setLevel(getattr(logging, self.log_level))
        self._root_logger.handlers.clear()

        self._setup_console_handler()

    def _setup_console_handler(self):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.log_level))
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(fmt)
        self._root_logger.addHandler(handler)

    def _log_dir(self, instance_id: str) -> Path:
        return self.output_dir / "logs" / instance_id

    def init_task(self, instance_id: str) -> Path:
        """Create log directory for a task and return it."""
        task_dir = self._log_dir(instance_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def write_task_log(self, instance_id: str, filename: str, content: str):
        """Write content to a task-specific log file."""
        task_dir = self._log_dir(instance_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / filename).write_text(content)

    def info(self, msg: str):
        self._root_logger.info(msg)

    def warning(self, msg: str):
        self._root_logger.warning(msg)

    def error(self, msg: str):
        self._root_logger.error(msg)

    def debug(self, msg: str):
        self._root_logger.debug(msg)
