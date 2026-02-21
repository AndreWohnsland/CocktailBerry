"""Generic Qt worker utilities for running callables in background threads."""

from __future__ import annotations

import contextlib
from collections.abc import Callable

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget

from src.ui.icons import IconSetter


class CallableWorker[T](QThread):
    """Generic worker thread that executes a callable and emits the result.

    This worker runs a provided callable in a background thread, keeping the
    Qt event loop responsive. When the callable completes, the result is
    emitted via the `finished` signal.

    Usage:
        worker = CallableWorker(lambda: service.fetch_data())
        worker.finished.connect(on_data_received)
        worker.start()

        ## For parameterized calls, use a lambda:
        worker = CallableWorker(
            lambda: service.process(arg1, arg2, keyword=value)
        )

    Note:
        The caller must keep a reference to the worker to prevent garbage collection
        before the work completes. Store it as an instance attribute (e.g., self._worker).

    """

    # Signal emits `object` since pyqtSignal doesn't support generics at runtime.
    # The actual type is T, determined by the callable's return type.
    finished = pyqtSignal(object)

    def __init__(self, func: Callable[[], T]) -> None:
        """Initialize the worker with a callable to execute.

        Args:
            func: A callable that takes no arguments and returns a value of type T.
                  Use a lambda to wrap functions that require arguments.

        """
        super().__init__()
        self._func = func

    def run(self) -> None:
        """Execute the callable and emit the result."""
        result: T = self._func()
        self.finished.emit(result)


def run_with_spinner[T](
    func: Callable[[], T],
    parent: QWidget,
    on_finish: Callable[[T], None] | None = None,
    disable_parent: bool = True,
) -> CallableWorker[T]:
    """Run a callable in a background thread with a spinner overlay.

    This is a convenience function that combines CallableWorker with a spinner
    overlay for visual feedback during long-running operations.

    Args:
        func: A callable that takes no arguments and returns a value of type T.
              Use a lambda to wrap functions that require arguments.
        parent: The widget to show the spinner on.
        on_finish: Optional callback that receives the result when work completes.
                   For void functions, use `lambda _: do_something()` to ignore the result.
        disable_parent: Whether to disable the parent widget while working.

    Returns:
        The CallableWorker instance. The caller MUST keep a reference to this
        (e.g., `self._worker = run_with_spinner(...)`) to prevent garbage collection.

    Example:
        With result handling::

            self._worker = run_with_spinner(
                lambda: service.fetch_data(),
                parent=self,
                on_finish=self._handle_result,
            )

        Fire-and-forget with cleanup callback (ignoring None result)::

            self._worker = run_with_spinner(
                update_os,
                parent=self,
                on_finish=lambda _: self._after_update(),
            )

    """
    icons = IconSetter()
    icons.start_spinner(parent, disable_parent)

    worker: CallableWorker[T] = CallableWorker(func)

    def on_worker_finished(result: T) -> None:
        if on_finish is not None:
            on_finish(result)
        # spinner might already be destroyed if parent is gone
        with contextlib.suppress(Exception):
            icons.stop_spinner()

    worker.finished.connect(on_worker_finished)
    worker.start()
    return worker
