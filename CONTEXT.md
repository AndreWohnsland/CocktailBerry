# CocktailBerry

CocktailBerry is open-source software for a DIY automated cocktail machine. It manages Cocktail definitions, dispenses them through configurable Dispensers and Hardware Extensions, and runs in two front-ends — a Qt desktop app (v1) and a React + FastAPI web app (v2) — over a shared Python core.

## Language

### Cocktail preparation

**Cocktail**:
A named drink defined by a list of Ingredients, an alcohol level, and a price. The same word covers both the stored definition and an instance being made or served.
_Avoid_: Recipe, drink

**Preparation**:
The act of producing a Cocktail — from validation, through dispensing, to a terminal state. The word covers both the in-flight act and the recorded history (an `EventType.COCKTAIL_PREPARATION` event). A Preparation ends as **finished**, **canceled**, or **failed** (e.g. ingredient shortage); these are states of one Preparation, not separate concepts.
_Avoid_: Brew, run, dispense job, drink-making

**Ingredient**:
A substance used in Cocktails (vodka, lime juice, …) with intrinsic properties: alcohol percentage, unit, cost. An Ingredient is independent of any machine; it becomes dispensable when placed in a Bottle.
_Avoid_: liquid, component

**Hand-add**:
An Ingredient added to a Cocktail by manual pouring rather than by the machine. In a Cocktail definition, an Ingredient is a Hand-add when no Bottle is assigned to it.
_Avoid_: manual add, hand ingredient

**Machine-add**:
An Ingredient delivered from a Bottle by its Dispenser during Preparation.
_Avoid_: auto-add, pump-add

**Virgin**:
A Cocktail served without its alcoholic Ingredients. A Cocktail's recipe declares whether a Virgin variant is permitted; if so, it can be prepared either with or without alcohol.
_Avoid_: non-alcoholic, mocktail, alcohol-free

### Machine & hardware

**Bottle**:
A numbered position on the machine that holds one Ingredient. Bottles are referenced by ID (e.g. "Bottle 3"). The word covers both the physical container and the slot it plugs into — CocktailBerry treats them as one concept.
_Avoid_: slot, container

**Dispenser**:
The mechanism that delivers an Ingredient from a Bottle during Preparation. Canonical term for any such mechanism (pumps, valves, future hardware). The Hardware Extension category of the same name is the abstraction that implements concrete Dispensers.
_Avoid_: spender, delivery mechanism

**Pump**:
A specific kind of Dispenser — a fluid pump driving liquid from a Bottle. Historically CocktailBerry only supported pumps, so much of the existing code and UI uses "pump" as shorthand for "dispenser." Going forward, prefer **Dispenser** as the general term and reserve **Pump** for situations where the dispenser is specifically a pump.
_Avoid_: motor; do **not** use Pump as a synonym for Dispenser in new code or docs

**Hardware Extension**:
A custom implementation of one of six hardware component categories, discovered at startup from `addons/<category>/` subfolders. Hardware Extensions implement an interface; they do not hook lifecycle events (that's an Addon's job). The categories are:

- **Hardware Context** — shared hardware instances (UART boards, SPI buses, custom controllers) accessible to other extensions
- **Scale** — weight measurement, used for weight-based recipes and dispense verification
- **Carriage** — moves the dispenser carriage for multi-position machines
- **Dispenser** — the hardware-extension category that implements concrete Dispensers (see term above)
- **RFID Reader** — reads NFC/RFID cards for payment, waiter login, or custom flows
- **LED** — drives indicator and ambient lighting

_Avoid_: hardware addon, hardware plugin

### Appearance (v2 web only)

**Theme**:
The named visual identity of the v2 web app — `default`, `berry`, `bavaria`, `alien`, `purple`, `tropical`, or `custom`. A Theme is a **machine-level** setting (`MAKER_THEME`): set once by the operator, shared by everyone who opens that machine's web app. It owns the *brand colors* (primary, secondary, danger, neutral). `custom` lets the operator pick those colors by hand.
_Avoid_: skin, style, palette (palette = the colors, Theme = the named choice)

**Mode**:
The light/dark axis of the v2 web app, orthogonal to Theme: any Theme can be shown in either Mode. Unlike Theme, Mode is **per-browser** (stored in localStorage, not on the machine) — each visitor chooses their own. Each shipped Theme defines its full palette — surface and role colors — explicitly for *both* Modes: the dark palette is the historical look, the light palette is the same Theme tuned to stay readable on a light surface (the brand identity is recognisable in both, the exact values differ). Text drawn on a colored fill uses the surface color and stays legible by contrast symmetry. The six shipped Themes are valid in both Modes; the **`custom` Theme opts out** — it is the operator's full-manual escape hatch (they pick an absolute background by hand), so Mode does not apply to it and the toggle is hidden while it is active.
_Avoid_: dark mode (that's one value of Mode, not the concept), color scheme

### Operations & admin

**Maker**:
The main cocktail-selection screen where a Cocktail is picked and a Preparation is started. Identified as `Tab.MAKER` in code. The "Maker" name is also the user-facing label for the act of making a cocktail (e.g. "go to the maker").
_Avoid_: home screen, main tab, cocktail screen

**Maker Password**:
A tab-level access gate (`UI_MAKER_PASSWORD`) that protects a configurable subset of tabs — typically Maker, Ingredients, Recipes, Bottles — from casual access. A Service Personnel member whose Role grants the matching tab permission bypasses this gate automatically.
_Avoid_: tab password, user password

**Master Password**:
The top-level admin gate (`UI_MASTERPASSWORD`) for the configuration / options window. A Service Personnel member whose Role grants the "Options" permission bypasses it. Strictly higher privilege than the Maker Password.
_Avoid_: admin password, root password, config password

**Addon**:
A third-party lifecycle extension that hooks into specific moments — startup, shutdown, before/after Preparation, or a continuous loop. Addons add optional features without bloating the core app (e.g. weight-based glass detection, cost-splitting checklists). Users install them by placing a Python file in `~/CocktailBerry/addons/`; an official curated list can also be managed in-app. Distinct from Hardware Extensions, which implement hardware interfaces rather than hook lifecycle.
_Avoid_: plugin, module, mod

**Service Personnel**:
A registered staff member who logs in via NFC Chip to operate the machine. Each Preparation is recorded against the logged-in Service Personnel, and per-tab permissions (Maker, Ingredients, Recipes, Bottles, Options) control which areas they can access and which password prompts they bypass.
_User-facing register_ (docs, UI strings, user conversations): **Service Personnel**.
_Code register_ (variable names, config keys like `WAITER_MODE`, internal logs): **Waiter** — shorter, identical in meaning. Not deprecated; both are correct in their respective contexts.
_Avoid_: bartender, operator, staff (when referring to this concept specifically)

**NFC Chip**:
The physical NFC/RFID tag assigned to a Service Personnel member. Scanning the chip on the machine's NFC reader logs that person in.
_Avoid_: card, tag, badge (use NFC Chip; "card" specifically refers to payment cards under NFC Payment)

**Role**:
A named set of permissions that can be assigned to one or more Service Personnel members. Roles control which tabs the member can access and which password prompts they bypass.
_Avoid_: permission set, group, access level

**Customer**:
The person paying for a Cocktail. Distinct from Service Personnel (the staff operating the machine). For NFC Payment, a Customer is represented by an NFC tag carrying a balance and an age flag; for SumUp Payment, a Customer is whoever taps a card on the terminal.
_Avoid_: user (overloaded — User would collide with Service Personnel), buyer, guest

**Payment**:
The umbrella feature that charges the Customer before a Preparation runs. Optional; off by default. Two implementations exist, never both at once: NFC Payment and SumUp Payment.
_Avoid_: charge, billing, transaction (use Payment)

**NFC Payment**:
Payment via an NFC tag scan. The tag's UID is sent to the Payment Service, which checks the Customer's balance and age flag and, if valid, authorises the Preparation and deducts the cost. Shares hardware with Service Personnel mode but the two cannot be enabled simultaneously.
_Avoid_: tag payment, card payment (Card Payment is ambiguous between this and SumUp)

**SumUp Payment**:
Payment via a SumUp Solo card terminal, routed through SumUp's cloud API. The Customer confirms the payment on the physical terminal. Requires both CocktailBerry and the terminal to be online.
_Avoid_: card payment, terminal payment

**Payment Service**:
The separate companion application ([CocktailBerry-Payment](https://github.com/AndreWohnsland/CocktailBerry-Payment)) that stores NFC-payment Customer records (UID, balance, age flag) and adjudicates each NFC Payment request. Reachable over the local network from CocktailBerry; not part of this repo.
_Avoid_: payment server, payment backend (use Payment Service)

**Event**:
A recorded entry in the machine's activity log, identified by an event type and timestamp. Events give the operator visibility into both human-driven actions (Preparation, Cleaning) and system-driven actions (shutdown, reboot, software/OS update). Events are viewed via the admin "events" tile.
_Avoid_: log entry, audit record, action

**Cleaning**:
A maintenance cycle that flushes selected Bottles with water or cleaner by running their Dispensers. Recorded as its own Event type. Distinct from Preparation: no Cocktail is produced and no Customer is charged.
_Avoid_: flush, wash, rinse

## Flagged ambiguities

These are terms where the codebase and the glossary disagree — the glossary's choice wins for new work, but readers should expect to see the legacy form in existing code.

- **Pump vs Dispenser**: Historically all dispensing was done by pumps, so most existing code and many UI strings say "pump." The current model supports other dispensing hardware too, so **Dispenser** is canonical. A **Pump** is one specific kind of Dispenser. In new code and docs, use *Dispenser* unless the mechanism is specifically a fluid pump.
- **Service Personnel vs Waiter**: Not a drift, a register split. User-facing text (docs, dialogs, UI) uses **Service Personnel**. Code, config keys (`WAITER_MODE`), and internal variables use **Waiter**. Both are correct, in their own context.
- **Cocktail vs Recipe**: The glossary collapses these to one term, **Cocktail**. Some UI strings still say "recipe" for template management ("recipe deleted", "all recipes enabled"); treat these as drift to be tidied over time, not a separate domain concept.
- **Bottle vs Slot**: User-facing text and code both call the numbered machine position a **Bottle**, even though strictly it's a slot the bottle plugs into. The conflation is deliberate; there is no separate "Slot" concept.
- **Customer vs User**: Be careful with "user" — in payment docs it sometimes means the Customer (NFC tag holder), but in any context involving the machine itself "user" reads as Service Personnel. Use **Customer** when referring to the person paying.

## Example dialogue

A new contributor (**Dev**) asks the maintainer (**Andre**) how a Cocktail gets made end-to-end.

> **Dev**: When someone walks up to the machine, what's the actual sequence?
>
> **Andre**: Depends what's configured. If Payment is on, they tap their NFC Chip first — for NFC Payment, the Payment Service checks the Customer's balance and age flag; for SumUp Payment, they confirm on the terminal. Alternatively, if Service Personnel mode is on, a staff member's NFC Chip has to already be logged in, and the Preparation is recorded against them.
>
> **Dev**: And then it dispenses?
>
> **Andre**: It runs a Preparation. For each Machine-add Ingredient, the Dispenser on that Bottle runs until the target amount is reached. Hand-add Ingredients are shown to the operator to pour manually. If a Bottle is short or someone cancels, the Preparation finishes as **failed** or **canceled** — either way it's logged as an Event.
>
> **Dev**: What if the Cocktail has rum but the Customer doesn't want alcohol?
>
> **Andre**: If the Cocktail has Virgin available, they pick the Virgin version. Alcoholic Ingredients are skipped. It's still the same Cocktail — just prepared without alcohol.
>
> **Dev**: And the Cleaning button on the admin screen?
>
> **Andre**: Same dispense path — the Dispensers run for selected Bottles — but no Cocktail, no Customer, no Payment. It's logged as its own Event type.
>
> **Dev**: I'm seeing the word "pump" everywhere in the code though.
>
> **Andre**: Yeah — legacy. We only had pumps for years. Now there are valves and other things, so we call them Dispensers. Code still mostly says "pump"; new code should say Dispenser unless it's specifically a fluid pump.
