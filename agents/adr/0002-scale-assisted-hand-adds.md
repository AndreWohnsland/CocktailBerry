# Scale-assisted hand adds

## Context

After machine pumping, ingredients that are not on a pump (`bottle is None`, the
"hand adds") have to be poured in by the user. Historically both versions just showed a
text message — `_build_comment_maker()` → `cocktail_ready` — listing `~10 ml X` (v1: a
`standard_box` dialog, v2: HTML in `ProgressModal`). The user eyeballed the amount.

CocktailBerry already has a core scale abstraction (`MachineController.scale_tare()` /
`scale_read_grams()` / `has_scale`, density assumed 1 g/ml) used for weight-based pump
dispensing. We want an opt-in flow that guides hand pours with the scale: a window that
lists the hand adds with a *measure* button on each weighable one; tapping it tares, then
tracks `current_grams / target_ml` on a progress bar until the target is reached, resolving
the row. The user can finish early.

## Decision

**Opt-in is a single global config flag** `MAKER_SCALE_FOR_HAND_ADDS` (default `False`),
effective only when `SCALE_CONFIG.enabled` (enforced in `_validate_scale_config`). It
applies to every cocktail uniformly — no per-recipe/per-ingredient schema change.

**The guidance window replaces the old text message for every cocktail that has hand
adds**, whether or not the scale is used. Each hand add is one row:

- A **weighable (ml) row is "measurable"** — it gets a scale measure button + progress bar —
  only when the feature is on **and** a scale is present. The `measurable` flag is computed
  once in `prepare_cocktail` and carried on each `HandAddMeasure`.
- Every other row (non-ml units like `pieces` / `dash`, or *any* row when the feature is
  off or no scale is present) is a **by-hand confirm** (a check button), with no scale
  interaction.

**Non-blocking, frontend-driven — no backend lock.** `prepare_cocktail` finalizes the
cocktail immediately after pumping (consumption, hooks, events, stats) and returns
`FINISHED`; it never waits on the pour. The hand-add list is published on
`shared.cocktail_status.hand_adds`, surfaced through the existing
`/cocktails/prepare/status` poll, so the v2 list is server-authoritative rather than
re-derived in the browser. The guidance window is purely post-hoc UI; v1/v2 divergence is
confined to the two windows, which deliberately mirror each other (gating, mechanics,
layout, icons):

- **v1** (`MainScreen.run_hand_add_measure` → `HandAddMeasureScreen`): a synchronous
  `processEvents()` poll loop on the main thread — mirroring how `make_cocktail` keeps the
  GUI responsive — reads the scale directly via `MachineController`. A walk-away timeout
  auto-closes it.
- **v2** (`HandAddMeasure` rendered inside `ProgressModal`): React drives the per-ingredient
  tare→read→progress loop client-side against the open `/scale/tare` + `/scale/read`
  endpoints. A walk-away timeout auto-closes it.

**Atomic publish of the terminal status.** The modal acts on *any* terminal status, so the
hand-add list (and the optional `additional_message`) are written onto
`shared.cocktail_status` **before** the status is flipped to `FINISHED`. That flip is owned
by `MachineController.make_cocktail`, which is the one place that creates the terminal
`CocktailStatus`; `prepare_cocktail` passes the pre-built list (and message) into it, and
the publish happens inside the existing `if status != CANCELED` block with the status flip
**last**. Because every reader gates on `status` first, a poll never observes a terminal
status without the accompanying list — and a canceled run never publishes a list, so it
never pops the guidance window.

**Consumption/stats are unchanged.** Hand-add consumption is still recorded as the recipe
amount (`set_handadd_consumption()`), regardless of actual poured weight — the scale here is
a pouring aid, not a metering change — so no measured values are plumbed back and historical
data stays comparable.

**Scale endpoints.** `/scale/tare` and `/scale/read` are non-destructive live reads, used by
both the guidance window and the calibration screen, so they are left open
(un-master-protected); only the config-mutating `/scale/calibrate` stays master-protected.

**Measure mechanics (both versions).** One ingredient at a time (single scale). Tapping
*measure* tares, then progress = `clamp(grams / target_ml * 100, 0, 100)`. Reaching the
target resolves the row in place; other rows stay locked while one measurement runs. A
cancel on the active row returns it to pending (re-tares next attempt). The window
auto-finishes once **every** row is resolved (lingering briefly on a completion message);
*Finish* is always available to close early.

## Consequences

- The feature is **non-blocking**: the machine reports `FINISHED` as soon as the pumps stop,
  so the busy-lock does **not** span the pour. On a multi-client v2 setup a second client
  could therefore start another cocktail (and tare/use the scale) while a user is still
  pouring hand adds. Accepted as low-risk for a single-station kiosk; **revisit if
  concurrent multi-station use becomes a goal.**
- Finalization stays centralized in `prepare_cocktail`; the only shared-module change is the
  `hand_adds` payload threaded through `make_cocktail`.
- `CocktailStatus` gains `hand_adds: list[HandAddMeasure]`.
- A walk-away timeout in each frontend auto-closes the (purely informational) window so an
  abandoned pour never leaves the UI stuck.

## Considered alternatives

- **Backend lock with a `WAITING_FOR_HAND_ADD` non-terminal status + a `threading.Event`
  the frontend signals via dedicated `/cocktails/prepare/handadd/{tare,read,finish}`
  endpoints** — an earlier design (and earlier draft of this ADR). Rejected during
  implementation as too heavy: it coupled the shared maker module to both UI layers and the
  API state machine, kept the machine busy through the pour, and needed a backend timeout so
  a closed browser could not wedge the machine forever. The non-blocking approach keeps the
  scale read loop a thin client concern and the backend only needs to publish the list.
- **Fully backend-driven state machine** (per-ingredient start/poll/finish endpoints,
  progress computed server-side) — rejected as heaviest; the scale read loop is naturally a
  thin client concern.
- **Per-cocktail / per-ingredient opt-in** — rejected: needs a DB migration and editor UI in
  both versions for a feature that is a global machine capability.
- **Recording actual poured grams as consumption** — deferred: more accurate stats but
  requires a measured-payload round-trip; not worth the plumbing for a pouring aid.
