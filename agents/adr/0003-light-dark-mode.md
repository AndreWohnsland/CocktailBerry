# Light/Dark Mode (v2 web)

## Context

The v2 web app has one visual axis today: **Theme** (`default`, `berry`, `bavaria`,
`alien`, `purple`, `tropical`, `custom`) — a machine-level setting (`MAKER_THEME`) applied
as `documentElement.className`, bridged into Tailwind via `@theme` (`--color-primary:
var(--primary-color)`, …). Each Theme defines five CSS vars; five of the six are dark,
`bavaria` is light (`#dad9d9`). There is no separate "text color" — body and element text
*is* the brand color (`html,body { color: var(--primary-color) }`; ~116 `text-{role}`
usages), and `custom` writes its five colors as **inline styles** on `documentElement`.

We want a light/dark toggle for v2 only (v1 Qt untouched). A community fork added one, but
bundled it with a full UI redesign (Radix, glassmorphism with 24 `backdrop-filter` layers,
web fonts, ~1600 LOC). We want the feature without the redesign, minimal footprint, no new
dependencies, and dark Mode pixel-identical to today.

## Decision

**Mode is a second, orthogonal axis to Theme**, named **Mode** (light/dark). It is
**per-browser** (localStorage `MODE`, default `dark`), *not* machine config — different
viewers of the same machine (kiosk, guest phones over the network) choose their own. Each
Theme authors its **full palette** (surface *and* role colors) explicitly per Mode: the
dark palette is today's look, the light palette is the same Theme retuned to read on a light
surface. Role colors therefore differ between Modes — the brand identity stays recognizable,
the exact values are tuned per surface.

- **Colors are authored explicitly per Theme × Mode, not derived.** Each Theme has a
  `.theme { … }` (dark = today's values, preserved) and a `.theme[data-mode="light"] { … }`
  block defining the six core tokens: `--background-color`, `--text-color`, and the four role
  colors `--primary/secondary/neutral/danger-color`. (An earlier draft derived the light
  values with `color-mix`/`oklch`; it gave too little control and odd threshold clipping, so
  we author them — it's a one-time cost and the values are tunable.)
- **No separate foreground variants.** A role color is authored per Mode to read on that
  Mode's surface, so the *same* token serves both foreground text (`text-primary`) and fills
  (`bg-primary`). This is why `--*-text-color` tokens were dropped — fewer token names.
- **On-fill text = the surface, by symmetry.** `--on-{role}-color` defaults to
  `var(--background-color)`. Because contrast is symmetric, any role color with enough
  contrast to be readable *as foreground on the surface* automatically has the same contrast
  *as the surface color on its fill* — so `text-on-{role}` is readable for free in both Modes.
  Override `--on-*-color` only where an intrinsically-light "pop" fill needs explicit dark
  text (none needed currently, since light-Mode pops are authored deep enough).
- **Backgrounds:** dark = each Theme's current value (preserved); light = `color-mix(in srgb,
  var(--primary-color) ~7–10%, #f5f6f7)` — a near-white surface tinted with the Theme's own
  primary (the tint percentage is tunable per Theme). **`bavaria` is the one Theme that
  changes** — it gains a newly-authored dark background; its old light look returns in light
  Mode. Only the light-surface tint uses `color-mix`, so the browser floor stays **Chromium
  111+** (no `oklch`/relative-color needed).
- **`custom` opts out of Mode entirely.** It is the operator's full-manual escape hatch (an
  absolute, hand-picked background). When `theme === 'custom'` the toggle is hidden and Mode
  is forced to `dark` (`effectiveMode = theme === 'custom' ? 'dark' : mode`), so the light
  overrides never apply — `custom` renders exactly as today. Its inline-style application and
  the `CUSTOM_COLOR_BACKGROUND` config field are unchanged (v1 still uses the field).
- **Mechanism:** `mode` state lives in the existing `ConfigProvider` (next to `theme`,
  which it needs for `effectiveMode`, and which already owns the apply-effect) — no new
  provider. Application is a `data-mode` attribute on `documentElement` **and `body`** (the
  Theme class is on both and redeclares the surface tokens, so `.theme[data-mode="light"]`
  must win on each). A small pre-paint inline script in `index.html` sets `data-mode` from
  localStorage to avoid a flash. **No `window` events** — plain React context.
- **Toggle UI:** an encapsulated sun/moon `<ModeToggle/>` in the Header (always
  ungated — Options is Master-Password gated, so the toggle cannot live there). Hidden when
  `custom`.

## Consequences

- Dark Mode is pixel-identical to today **except `bavaria`**, which defaults to its new dark
  variant after upgrade (toggle to light for the old look).
- Footprint: per-Theme light blocks in `themes.css` (~6 values each, one-time), a small
  component, and a few lines in `ConfigProvider` / `index.html`. The 22 `text-on-{role}`
  spots stay; the foreground `text-{role}` usages are unchanged (the brief `*-text` rename
  from the derivation draft was reverted). **No new dependencies.**
- Only the light-surface tint uses `color-mix` (Chromium 111+). If a deployed Pi runs an
  older Chromium, the light backgrounds fall back; everything else is plain colors.
- Token names dropped from ~14 (derivation draft) to the 6 core + 4 `--on-*` (mostly aliased
  to the surface), which is what makes the model maintainable per Theme.

## Considered alternatives

- **The fork's approach** (Radix + glassmorphism + per-Theme hand-authored tokens + a
  `window 'cb-mode-change'` event syncing manual DOM writes) — rejected: ~1600 LOC and 7
  deps for a redesign that wasn't asked for; `backdrop-filter` × 24 is a known Raspberry-Pi
  performance risk; the event/DOM state bypasses the app's context pattern. We landed on the
  same explicit per-Theme/Mode authoring it used, but without the redesign or extra deps.
- **Deriving the palette in CSS** (`color-mix` foreground darkening + `oklch` relative-color
  auto-contrast for on-fill) — built and rejected: too little control, hard threshold
  clipping looked odd when toggling, and `oklch` raised the browser floor to Chromium 119+.
  Explicit per-Mode values give control for a modest one-time authoring cost.
- **Mode as machine config (`MAKER_*`)** — rejected: it is inherently per-viewer, and the
  per-browser store matches how `THEME` is already mirrored client-side.
- **Follow OS `prefers-color-scheme` for the default** — rejected (for now): adds a third
  "system" state and risks changing existing dark installs on upgrade if a kiosk reports
  light. Default `dark` preserves today's look; OS-following is a trivial later add.
- **Per-Theme light backgrounds / surface+card depth** — rejected as bloat; one tinted
  formula suffices, brand colors carry identity.
- **Mode for `custom`** — rejected: would force derived backgrounds onto the one Theme whose
  purpose is absolute manual control, removing its arbitrary-background capability for a user
  who didn't ask. Trivially reversible if wanted later.
