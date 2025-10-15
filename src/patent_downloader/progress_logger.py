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

    def log_message(self, message: str, level: str = "info", force_show: bool = False) -> None:
        """Log message without interfering with progress bar.

        Args:
            message: Message content
            level: Message level (error, warning, info, debug, success)
            force_show: Whether to force display, ignoring log level restrictions
        """
        # Filter based on current log level
        current_log_level = logging.getLogger().level

        # Map level strings to logging levels

        # Special handling: display error and warning messages in ERROR level (default), unless forced
        if current_log_level == logging.ERROR and not force_show:
            # In ERROR mode, display error and warning messages
            if level not in ["error", "warning"]:
                return
        # In WARNING level, display error, warning and info messages, unless forced
        elif current_log_level == logging.WARNING and not force_show:
            if level not in ["error", "warning"]:
                return
        # INFO level and above display all messages
        else:
            pass  # Display all messages

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

            # Use unified progress icon, not changing with individual patent status
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
            # Use global UI level for filtering
            ui_level = get_ui_level()

            if record.levelno >= ui_level:
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


# Global UI level for filtering
_ui_level: int = logging.ERROR

# Global progress logger instance
_progress_logger: Optional[ProgressLogger] = None


def get_ui_level() -> int:
    """Get current UI level."""
    return _ui_level


def set_ui_level(level: int) -> None:
    """Set UI level."""
    global _ui_level
    _ui_level = level


def get_progress_logger() -> ProgressLogger:
    """Get the global progress logger instance."""
    global _progress_logger
    if _progress_logger is None:
        _progress_logger = ProgressLogger()
    return _progress_logger


def setup_progress_logging(verbose_level: int = 0) -> ProgressLogger:
    """Setup logging with progress bar support.

    Args:
        verbose_level: Verbosity level (0=ERROR, 1=WARNING+, 2=INFO+, 3=DEBUG+)
    """
    progress_logger = get_progress_logger()

    # Configure root logger based on verbose level
    # Root logger level set to WARNING so both WARNING and ERROR messages can reach the handler
    # But UI display will be filtered based on verbose_level
    if verbose_level >= 3:
        ui_level = logging.DEBUG
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    elif verbose_level >= 2:
        ui_level = logging.INFO
        formatter = logging.Formatter("%(name)s - %(message)s")
    elif verbose_level >= 1:
        ui_level = logging.WARNING  # -v shows WARNING and ERROR
        formatter = logging.Formatter("%(name)s - %(message)s")
    else:
        # Level 0 (default): Only show ERROR, don't show WARNING
        # User requirement: don't show WARNING by default, need verbose to display
        ui_level = logging.ERROR  # UI only shows ERROR
        formatter = logging.Formatter("%(name)s - %(message)s")

    # Set global UI level
    set_ui_level(ui_level)

    root_logger = logging.getLogger()
    # Key: root logger level must be set to allow WARNING through
    root_logger.setLevel(logging.WARNING)  # Always allow WARNING and ERROR through

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our custom handler
    handler = ProgressLogHandler(progress_logger)
    handler.setLevel(logging.DEBUG)  # Accept all log levels
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return progress_logger
