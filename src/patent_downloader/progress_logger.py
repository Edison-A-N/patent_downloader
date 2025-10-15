"""Progress bar and logging coordination utility."""

import logging
import sys
import threading
from typing import Optional


class ProgressLogger:
    """Manages progress bar display and log output coordination."""

    def __init__(self):
        self._lock = threading.Lock()
        self._current_line = ""
        self._progress_active = False
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def start_progress(self, total: int, current: int = 0) -> None:
        """Start displaying progress bar."""
        with self._lock:
            self._progress_active = True
            self._update_progress_line(current, total)

    def update_progress(self, current: int, total: int, patent_number: str = "", success: bool = True) -> None:
        """Update progress bar display."""
        with self._lock:
            if self._progress_active:
                self._update_progress_line(current, total, patent_number, success)

    def finish_progress(self) -> None:
        """Finish progress bar display."""
        with self._lock:
            if self._progress_active:
                self._clear_current_line()
                self._progress_active = False

    def log_message(self, message: str, level: str = "info") -> None:
        """Log message without interfering with progress bar."""
        with self._lock:
            # Clear current progress line
            if self._progress_active:
                self._clear_current_line()

            # Print log message
            if level == "error":
                print(f"❌ {message}", file=sys.stderr)
            elif level == "warning":
                print(f"⚠️  {message}", file=sys.stderr)
            elif level == "success":
                print(f"✅ {message}")
            else:
                print(f"ℹ️  {message}")

            # Restore progress line
            if self._progress_active:
                self._restore_current_line()

    def _update_progress_line(self, current: int, total: int, patent_number: str = "", success: bool = True) -> None:
        """Update the progress bar line."""
        if total > 0:
            percentage = int((current / total) * 100)
            bar_length = 40
            filled_length = int(bar_length * current // total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            # 使用统一的进度图标，不随单个专利状态变化
            progress_icon = "▶️"
            patent_status = " ✅" if success else " ❌" if patent_number else ""
            patent_info = f" [{patent_number}]{patent_status}" if patent_number else ""

            self._current_line = f"\r{progress_icon} {bar} {percentage}% ({current}/{total}){patent_info}"
        else:
            self._current_line = f"\rProgress: {current} processed"

        print(self._current_line, end="", flush=True)

    def _clear_current_line(self) -> None:
        """Clear the current line."""
        print("\r" + " " * len(self._current_line) + "\r", end="", flush=True)

    def _restore_current_line(self) -> None:
        """Restore the current progress line."""
        print(self._current_line, end="", flush=True)


class ProgressLogHandler(logging.Handler):
    """Custom logging handler that works with progress bar."""

    def __init__(self, progress_logger: ProgressLogger):
        super().__init__()
        self.progress_logger = progress_logger

    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record through progress logger."""
        try:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                self.progress_logger.log_message(msg, "error")
            elif record.levelno >= logging.WARNING:
                self.progress_logger.log_message(msg, "warning")
            elif record.levelno >= logging.INFO:
                self.progress_logger.log_message(msg, "info")
            else:
                self.progress_logger.log_message(msg, "debug")
        except Exception:
            self.handleError(record)


# Global progress logger instance
_progress_logger: Optional[ProgressLogger] = None


def get_progress_logger() -> ProgressLogger:
    """Get the global progress logger instance."""
    global _progress_logger
    if _progress_logger is None:
        _progress_logger = ProgressLogger()
    return _progress_logger


def setup_progress_logging(verbose: bool = False) -> ProgressLogger:
    """Setup logging with progress bar support."""
    progress_logger = get_progress_logger()

    # Configure root logger
    level = logging.DEBUG if verbose else logging.WARNING
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our custom handler
    handler = ProgressLogHandler(progress_logger)
    handler.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(message)s")
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return progress_logger
