# Scale-assisted hand adds

## Context

After machine pumping, ingredients that are not on a pump (`bottle is None`, the
"hand adds") have to be poured in by the user. Today both versions just show a text
message — `_build_comment_maker()` → `cocktail_ready` — listing `~10 ml X` (v1: a
`standard_box` dialog, v2: HTML in `ProgressModal`). The user eyeballs the amount.

CocktailBerry already has a core scale abstraction (`MachineController.scale_tare()` /
`scale_read_grams()` / `has_scale`, density assumed 1 g/ml) used for weight-based pump
dispensing. We want an opt-in flow that guides hand pours with the scale: a window that
lists the hand adds with a *measure* button each; tapping it tares, then tracks
`current_grams / target_ml` on a progress bar until the target is reached, removing the
row. The user can finish early.

Two constraints shaped the design:

- `prepare_cocktail()` in `src/tabs/maker.py` is **shared** between v1 and v2 and runs
  machine-prep → finalization in one pass. The new measure phase is interactive and sits
  *between* those, but its UI is version-specific (v1: synchronous Qt loop on the main
  thread; v2: a background thread that must wait for a browser-driven UI).
- The existing `/scale/*` endpoints are **master-protected** (admin only), so the maker
  UI cannot reuse them during preparation.
- `shared.cocktail_status` is the single "machine busy" lock. If prep reported `FINISHED`
  the moment the pumps stop, a second client could start another cocktail and tare/use the
  same scale mid-pour.

## Decision

**Opt-in is a single global config flag** `MAKER_SCALE_FOR_HAND_ADDS` (default `False`),
effective only when `SCALE_CONFIG.enabled` (enforced in `_validate_scale_config`). It
applies to every cocktail uniformly — no per-recipe/per-ingredient schema change.

**Trigger.** The measure window replaces the text message only when the cocktail has at
least one **weighable (ml) hand add**. Non-ml hand adds (`2 pieces mint`, `3 dash bitters`)
are listed inside the window as static instructions with no measure button. Cocktails with
only non-ml hand adds, or none, keep the current text path.

**Lifecycle — backend lock + frontend-driven loop.** After pumping, when the flow applies,
preparation enters a new non-terminal status `PrepareResult.WAITING_FOR_HAND_ADD`, keeping
the machine "busy" (blocks `validate_cocktail`). The shared finalization (consumption,
hooks, events) runs **once**, after the measure phase ends. Hand-add consumption is still
recorded as the recipe amount (`set_handadd_consumption()` unchanged) regardless of actual
poured weight — the scale here is a pouring aid, not a metering change — so no measured
values are plumbed back.

**Seam — callback injection.** `prepare_cocktail()` gains a
`hand_add_runner: Callable[[Cocktail], None] | None`. To avoid threading it through every
call site, a module-level fallback `maker.HAND_ADD_RUNNER` is registered once per frontend
at startup; the explicit param is kept for tests. `prepare_cocktail` decides *whether* to
run it (feature on + `mc.has_scale` + ≥1 ml hand add + not canceled); the runner decides
*how*:

- **v1** (`MainScreen.run_hand_add_measure`): shows `HandAddMeasureScreen` and runs a
  synchronous `processEvents()` poll loop on the main thread — mirroring how
  `make_cocktail` keeps the GUI responsive — reading the scale directly. Returns on
  finish/auto-finish.
- **v2** (`web_hand_add_runner`): sets `WAITING_FOR_HAND_ADD` + the hand-add list on
  `shared.cocktail_status`, then blocks on `shared.hand_add_finished` (a
  `threading.Event`) with a timeout. React drives the per-ingredient tare→read→progress
  loop client-side via new **maker-protected**, status-guarded endpoints
  (`/cocktails/prepare/handadd/{tare,read,finish}`); the finish endpoint sets the Event.

**Measure mechanics (both versions).** One ingredient at a time (single scale). Tapping
*measure* tares, then progress = `clamp(grams / target_ml * 100, 0, 100)`. Reaching the
target auto-removes the row; a cancel/back on the active row returns it to pending
(re-tares next attempt) while other rows stay locked. The phase **auto-finishes** when all
rows are ml and all done; if any text-only row exists it waits for an explicit *Finish*,
which is always available.

## Consequences

- The busy-lock holds through the pour; no second cocktail can corrupt the scale. The
  v2 background task blocks up to a timeout (`HAND_ADD_TIMEOUT_S`) so a closed browser
  cannot wedge the machine forever — on timeout it finalizes as if finished.
- Finalization stays centralized in `prepare_cocktail`; the only shared-module addition is
  the runner hook. v1/v2 divergence is confined to the two runners.
- `CocktailStatus` gains `hand_adds: list[HandAddMeasure]`, surfaced through the existing
  `/cocktails/prepare/status` poll, so the v2 list is authoritative (server-scaled amounts)
  rather than re-derived in the browser.
- Consumption/stats semantics are unchanged, so historical data stays comparable.

## Considered alternatives

- **Per-cocktail / per-ingredient opt-in** — rejected: needs a DB migration and editor UI
  in both versions for a feature that is a global machine capability.
- **Fully frontend-driven, no lock** (prep `FINISHED` right after pumps, pure client-side
  measure via scale endpoints) — rejected: loses the machine-busy guarantee; a second
  client could tare/use the scale mid-pour.
- **Fully backend-driven state machine** (per-ingredient start/poll/finish endpoints,
  progress computed server-side) — rejected as heaviest; the scale read loop is naturally a
  thin client concern and the backend only needs the busy-lock + a done signal.
- **Recording actual poured grams** as consumption — deferred: more accurate stats but
  requires a measured-payload round-trip; not worth the plumbing for a pouring aid.
- **Branching on `w` inside `prepare_cocktail`** instead of a callback — rejected: couples
  the shared maker module to both UI layers and API state.
