"""
Progress tracking for long-running operations.

Provides user feedback during data extraction and analysis.
"""

from typing import Optional, Iterator
from contextlib import contextmanager

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from ..logger import get_logger

logger = get_logger()


class ProgressTracker:
    """
    Manages progress bars for long operations.

    Falls back to logging if tqdm not available.
    """

    def __init__(
        self,
        total: Optional[int] = None,
        desc: str = "Processing",
        disable: bool = False,
    ):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items (None for unknown)
            desc: Description of the operation
            disable: Disable progress display
        """
        self.total = total
        self.desc = desc
        self.disable = disable
        self.current = 0

        if TQDM_AVAILABLE and not disable:
            self.pbar = tqdm(total=total, desc=desc, unit="item")
        else:
            self.pbar = None
            if not disable:
                logger.info(f"{desc}...")

    def update(self, n: int = 1) -> None:
        """
        Update progress.

        Args:
            n: Number of items completed
        """
        self.current += n

        if self.pbar is not None:
            self.pbar.update(n)
        elif not self.disable and self.total:
            # Log every 10%
            if int((self.current - n) / self.total * 10) < int(self.current / self.total * 10):
                pct = int(self.current / self.total * 100)
                logger.info(f"{self.desc}: {pct}% complete")

    def set_description(self, desc: str) -> None:
        """Update description."""
        self.desc = desc
        if self.pbar is not None:
            self.pbar.set_description(desc)

    def close(self) -> None:
        """Close progress bar."""
        if self.pbar is not None:
            self.pbar.close()
        elif not self.disable:
            logger.info(f"{self.desc}: Complete")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


@contextmanager
def progress_bar(
    iterable: Optional[Iterator] = None,
    total: Optional[int] = None,
    desc: str = "Processing",
    disable: bool = False,
):
    """
    Context manager for progress tracking.

    Args:
        iterable: Iterable to wrap (if provided)
        total: Total items (required if iterable not provided)
        desc: Operation description
        disable: Disable progress display

    Yields:
        Progress tracker or wrapped iterable

    Example:
        # With iterable
        with progress_bar(items, desc="Processing items") as items_iter:
            for item in items_iter:
                process(item)

        # Manual updates
        with progress_bar(total=100, desc="Processing") as tracker:
            for i in range(100):
                process(i)
                tracker.update()
    """
    if iterable is not None and TQDM_AVAILABLE and not disable:
        # Wrap iterable with tqdm
        yield tqdm(iterable, desc=desc, total=total)
    elif iterable is not None:
        # Just return iterable without progress
        if not disable:
            logger.info(f"{desc}...")
        yield iterable
        if not disable:
            logger.info(f"{desc}: Complete")
    else:
        # Manual progress tracking
        tracker = ProgressTracker(total=total, desc=desc, disable=disable)
        try:
            yield tracker
        finally:
            tracker.close()
