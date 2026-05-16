from __future__ import annotations

import heapq
import time
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.logger_handler import LoggerHandler
from src.machine.dispensers.base import BaseDispenser

if TYPE_CHECKING:
    from src.machine.carriage import CarriageInterface
    from src.models import Ingredient

_logger = LoggerHandler("DispenserScheduler")

SchedulerProgressCallback = Callable[[int], None]
"""Callback signature: (progress_percent) -> None"""

CancelCheck = Callable[[], bool]
"""Returns True if the preparation should be cancelled."""

_POLL_INTERVAL = 0.05
"""How often (seconds) the schedulers' inner loops check elapsed time and cancellation."""

_PROGRESS_COMPLETE = 100
"""Maximum progress value emitted via on_progress callbacks (100 = done)."""


@dataclass
class PreparationItem:
    """A single dispensing task for the scheduler."""

    dispenser: BaseDispenser
    amount_ml: float
    pump_speed: int
    estimated_time: float = 0.0
    consumption: float = 0.0
    done: bool = False
    recipe_order: int = 1
    ingredient: Ingredient | None = None
    """Back-reference to the source ingredient. None for non-ingredient tasks like cleaning."""
    revert: bool = False

    def __post_init__(self) -> None:
        if self.estimated_time > 0.0:
            return
        divisor = self.dispenser.volume_flow * self.pump_speed / 100
        if divisor == 0:
            return
        self.estimated_time = self.amount_ml / divisor


@dataclass
class CleaningItem:
    """A single time-based cleaning task for the CleaningScheduler."""

    dispenser: BaseDispenser
    duration_seconds: float
    revert: bool = False


CarriageItem = PreparationItem | CleaningItem
"""Either kind of scheduler item — both expose ``dispenser.carriage_position``."""

CarriageRunOne = Callable[[CarriageItem, int, int], None]
"""``(item, index, total) -> None`` callback invoked once per carriage-positioned item."""


class BaseScheduler:
    """Shared infrastructure for both schedulers.

    Owns the constructor and the carriage-sequence template method
    (``move_to → on_each → sleep wait_after_dispense``). Does NOT call
    ``home()`` — each subclass's ``run()`` owns when to home.
    """

    def __init__(self, max_concurrent: int, carriage: CarriageInterface | None = None) -> None:
        self.max_concurrent = max_concurrent
        self._carriage = carriage

    def _run_carriage_sequence(
        self,
        ordered_items: Sequence[CarriageItem],
        on_each: CarriageRunOne,
        is_cancelled: CancelCheck,
    ) -> None:
        """Iterate carriage-positioned items: move → on_each(item, idx, total) → wait."""
        if self._carriage is None:
            raise ValueError("Carriage is required for this operation")
        total = len(ordered_items)
        for idx, item in enumerate(ordered_items):
            if is_cancelled():
                break
            self._carriage.move_to(item.dispenser.carriage_position)
            on_each(item, idx, total)
            if self._carriage.wait_after_dispense > 0 and not is_cancelled():
                time.sleep(self._carriage.wait_after_dispense)


class DispenserScheduler(BaseScheduler):
    """Schedules and runs dispenser tasks with greedy slot-filling.

    Responsibilities:
    - Groups items by recipe_order (sequential across groups)
    - Within each group: parallel dispensers run with greedy scheduling (longest first),
      then exclusive dispensers run one-by-one
    - Manages threading, progress aggregation, and cancellation
    """

    def __init__(self, max_concurrent: int, carriage: CarriageInterface | None = None) -> None:
        super().__init__(max_concurrent, carriage)
        self._next_log_time = 0.0

    def run(
        self,
        items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Execute all preparation items respecting scheduling constraints."""
        if not items:
            return

        self._next_log_time = 0.0
        # Emit initial 0% so the UI refreshes before any long blocking step
        # (notably the carriage moving to the first position).
        on_progress(0)
        groups = _group_by_recipe_order(items)
        if self._carriage is not None:
            groups = [_order_by_carriage_position(g, self._carriage.home_position) for g in groups]

        for group in groups:
            if is_cancelled():
                break
            if self._carriage is not None:
                self._run_group_with_carriage(group, items, on_progress, is_cancelled)
            else:
                self._run_group(group, items, on_progress, is_cancelled)

        if self._carriage is not None:
            self._carriage.home()

    def _run_group(
        self,
        group: list[PreparationItem],
        all_items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run a single recipe_order group.

        Order: parallel dispensers first (greedy), then exclusive dispensers one-by-one.
        """
        parallel = [item for item in group if not item.dispenser.needs_exclusive]
        exclusive = [item for item in group if item.dispenser.needs_exclusive]

        if parallel:
            self._run_parallel(parallel, all_items, on_progress, is_cancelled)
        for item in exclusive:
            if is_cancelled():
                break
            self._run_exclusive(item, all_items, on_progress, is_cancelled)

    def _run_group_with_carriage(
        self,
        group: list[PreparationItem],
        all_items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run a group sequentially with carriage positioning before each item."""

        def on_each(item: CarriageItem, _idx: int, _total: int) -> None:
            assert isinstance(item, PreparationItem)
            self._run_exclusive(item, all_items, on_progress, is_cancelled)

        self._run_carriage_sequence(group, on_each=on_each, is_cancelled=is_cancelled)

    def _run_parallel(
        self,
        items: list[PreparationItem],
        all_items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run parallel dispensers with greedy scheduling (longest first, fill freed slots)."""
        queue = list(items)  # Already sorted by estimated_time desc
        active: dict[Future[None], PreparationItem] = {}

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            while queue and len(active) < self.max_concurrent:
                data = queue.pop(0)
                future = executor.submit(_dispense_item, data)
                active[future] = data

            while active:
                if is_cancelled():
                    for data in active.values():
                        data.dispenser.stop()
                    break

                done_futures = [f for f in active if f.done()]
                for f in done_futures:
                    try:
                        f.result()
                    except Exception:
                        _logger.error(f"Dispenser error: {f.exception()}")
                    del active[f]
                    if queue:
                        next_data = queue.pop(0)
                        new_future = executor.submit(_dispense_item, next_data)
                        active[new_future] = next_data

                self._emit_progress(all_items, on_progress)
                time.sleep(_POLL_INTERVAL)

    def _run_exclusive(
        self,
        item: PreparationItem,
        all_items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run a single exclusive dispenser (blocking, no concurrency)."""
        if is_cancelled():
            return
        _dispense_item(item, on_step=lambda: self._emit_progress(all_items, on_progress))

    def _emit_progress(
        self,
        all_items: list[PreparationItem],
        on_progress: SchedulerProgressCallback,
    ) -> None:
        total_required = sum(x.amount_ml for x in all_items)
        total_consumed = sum(x.consumption for x in all_items)
        progress = (
            min(int(total_consumed / total_required * _PROGRESS_COMPLETE), _PROGRESS_COMPLETE)
            if total_required > 0
            else 0
        )
        consumption = [x.consumption for x in all_items]
        on_progress(progress)
        self._log_consumption(consumption, progress)

    def _log_consumption(self, consumption: list[float], progress: int) -> None:
        now = time.perf_counter()
        if now < self._next_log_time:
            return
        self._next_log_time = now + 1.0
        pretty = [round(x) for x in consumption]
        _logger.debug(f"{progress:>2}% | Volumes: {pretty}")


def _dispense_item(item: PreparationItem, on_step: Callable[[], None] | None = None) -> None:
    """Run one dispenser; mutate item.consumption/done; log and swallow exceptions.

    Shared by the parallel pool path (``on_step=None``; aggregate progress is
    emitted by the outer polling loop) and the exclusive/carriage path
    (``on_step`` emits aggregate progress on every consumption update).
    """

    def callback(consumption_ml: float, is_done: bool) -> None:
        item.consumption = consumption_ml
        item.done = is_done
        if on_step is not None:
            on_step()

    try:
        item.consumption = item.dispenser.dispense(
            amount_ml=item.amount_ml,
            pump_speed=item.pump_speed,
            revert=item.revert,
            callback=callback,
        )
        item.done = True
    except Exception as exc:
        _logger.error(f"Dispenser error on slot {item.dispenser.slot}: {exc}")


def _group_by_recipe_order(items: list[PreparationItem]) -> list[list[PreparationItem]]:
    """Group items by recipe_order, sorted by estimated_time descending within each group."""
    unique_orders = sorted({x.recipe_order for x in items})
    groups: list[list[PreparationItem]] = []
    for order in unique_orders:
        group = [x for x in items if x.recipe_order == order]
        group.sort(key=lambda x: x.estimated_time, reverse=True)
        groups.append(group)
    return groups


def estimate_total_time(groups: list[list[PreparationItem]], max_concurrent: int) -> float:
    """Estimate total preparation time across all recipe_order groups."""
    total = 0.0
    for group in groups:
        parallel_times = [x.estimated_time for x in group if not x.dispenser.needs_exclusive]
        exclusive_times = [x.estimated_time for x in group if x.dispenser.needs_exclusive]
        total += _estimate_group_time(parallel_times, max_concurrent)
        total += sum(exclusive_times)
    return round(total, 2)


def _estimate_group_time(estimated_times: list[float], max_concurrent: int) -> float:
    """Estimate makespan for parallel items using LPT (Longest Processing Time) scheduling."""
    if not estimated_times:
        return 0.0
    sorted_times = sorted(estimated_times, reverse=True)
    num_slots = min(max_concurrent, len(sorted_times))
    slots = [0.0] * num_slots
    heapq.heapify(slots)
    for t in sorted_times:
        earliest = heapq.heappop(slots)
        heapq.heappush(slots, earliest + t)
    return max(slots)


def estimate_carriage_time(
    groups: list[list[PreparationItem]],
    carriage: CarriageInterface,
    home_position: int,
) -> float:
    """Estimate total preparation time in carriage mode.

    Sums dispense times and carriage travel times between positions.
    """
    total = 0.0
    current_pos = home_position
    for group in groups:
        for item in group:
            pos = item.dispenser.carriage_position
            total += carriage.travel_time(current_pos, pos)
            total += item.estimated_time
            total += carriage.wait_after_dispense
            current_pos = pos
    # Return home after last item
    total += carriage.travel_time(current_pos, home_position)
    return round(total, 2)


def _order_by_carriage_position[DispatchItem: (PreparationItem, CleaningItem)](
    items: list[DispatchItem], home_position: int
) -> list[DispatchItem]:
    """Order items to minimize total carriage travel distance.

    Since positions are on a 1D line (0-100), the optimal order is a monotonic
    sweep from the starting point. We choose the sweep direction (ascending or
    descending) that results in less total travel from home through all
    positions and back to home.
    """
    if not items:
        return []
    ascending = sorted(items, key=lambda x: x.dispenser.carriage_position)
    descending = list(reversed(ascending))
    if _total_travel(ascending, home_position) <= _total_travel(descending, home_position):
        return ascending
    return descending


def _total_travel(items: Sequence[PreparationItem | CleaningItem], home_position: int) -> int:
    """Calculate total carriage travel: home -> items in order -> home."""
    if not items:
        return 0
    positions = [x.dispenser.carriage_position for x in items]
    total = abs(positions[0] - home_position)
    for i in range(1, len(positions)):
        total += abs(positions[i] - positions[i - 1])
    total += abs(positions[-1] - home_position)
    return total


# ---------------------------------------------------------------------------
# Cleaning scheduler — time-based, no volume/scale logic
# ---------------------------------------------------------------------------

_CLEANING_LARGE_AMOUNT = 2000
"""Sentinel amount that ensures a dispenser never self-terminates during cleaning.

The scheduler is responsible for stopping dispensers after the configured
wall-clock duration, so the amount passed to dispense() must never be
reached naturally.
"""


class CleaningScheduler(BaseScheduler):
    """Schedules time-based pump cleaning.

    Each dispenser runs for a fixed wall-clock duration — no volume
    calculations or scale interaction. In parallel mode, items are
    processed in batches of up to *max_concurrent*. With a carriage,
    items run sequentially with position moves between each.
    """

    def run(
        self,
        items: list[CleaningItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Execute all cleaning items."""
        if not items:
            return
        # Emit initial 0% so the UI refreshes before any long blocking step
        # (notably the carriage moving to the first position).
        on_progress(0)
        if self._carriage is not None:
            ordered = _order_by_carriage_position(items, self._carriage.home_position)
            self._run_with_carriage(ordered, on_progress, is_cancelled)
            self._carriage.home()
        else:
            self._run_parallel(items, on_progress, is_cancelled)

    def _run_parallel(
        self,
        items: list[CleaningItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run items in parallel batches, emitting overall progress."""
        batches = [items[i : i + self.max_concurrent] for i in range(0, len(items), self.max_concurrent)]
        n_batches = len(batches)
        for batch_idx, batch in enumerate(batches):
            if is_cancelled():
                break
            base = batch_idx * _PROGRESS_COMPLETE // n_batches
            ceiling = (batch_idx + 1) * _PROGRESS_COMPLETE // n_batches
            self._run_timed(batch, on_progress, is_cancelled, base_progress=base, max_progress=ceiling)

    def _run_with_carriage(
        self,
        ordered_items: Sequence[CleaningItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
    ) -> None:
        """Run items sequentially with carriage positioning before each."""

        def on_each(item: CarriageItem, idx: int, total: int) -> None:
            assert isinstance(item, CleaningItem)
            base = idx * _PROGRESS_COMPLETE // total
            ceiling = (idx + 1) * _PROGRESS_COMPLETE // total
            self._run_timed([item], on_progress, is_cancelled, base_progress=base, max_progress=ceiling)

        self._run_carriage_sequence(ordered_items, on_each=on_each, is_cancelled=is_cancelled)

    def _run_timed(
        self,
        batch: list[CleaningItem],
        on_progress: SchedulerProgressCallback,
        is_cancelled: CancelCheck,
        base_progress: int,
        max_progress: int,
    ) -> None:
        """Start all dispensers in *batch*, wait for duration, then stop all.

        Uses a sentinel large amount so dispensers never self-terminate —
        the scheduler drives the stop after the wall-clock duration elapses.
        """
        duration = batch[0].duration_seconds
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [
                executor.submit(
                    item.dispenser.dispense, _CLEANING_LARGE_AMOUNT, _PROGRESS_COMPLETE, item.revert, lambda *_: None
                )
                for item in batch
            ]
            start = time.perf_counter()
            while True:
                elapsed = time.perf_counter() - start
                if elapsed >= duration or is_cancelled():
                    for item in batch:
                        item.dispenser.stop()
                    break
                fraction = elapsed / duration
                on_progress(base_progress + int(fraction * (max_progress - base_progress)))
                time.sleep(_POLL_INTERVAL)
            for f in futures:
                try:
                    f.result(timeout=2.0)
                except Exception as exc:
                    _logger.error(f"Cleaning dispenser error: {exc}")
        if not is_cancelled():
            on_progress(max_progress)
