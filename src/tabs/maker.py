"""Module with all necessary functions for the maker Tab.

This includes all functions for the Lists, DB and Buttons/Dropdowns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.config.config_manager import CONFIG as cfg
from src.config.config_manager import Tab, shared
from src.database_commander import DatabaseCommander
from src.dialog_handler import DIALOG_HANDLER as DH
from src.logger_handler import LoggerHandler
from src.machine.controller import MachineController
from src.models import Cocktail, CocktailStatus, EventType, Ingredient, PrepareResult
from src.programs.addons import ADDONS
from src.service.waiter_service import WaiterService
from src.service_handler import SERVICE_HANDLER

if TYPE_CHECKING:
    from src.ui.setup_mainwindow import MainScreen

_logger = LoggerHandler("maker_module")


def _build_comment_maker(cocktail: Cocktail) -> str:
    """Build the additional comment for the completion message (if there are handadds)."""
    comment = ""
    hand_add = cocktail.handadds
    # sort by descending length of the name and unit combined
    length_desc = sorted(hand_add, key=lambda x: len(x.name) + len(x.unit), reverse=True)
    for ing in length_desc:
        amount: int | float = ing.amount
        if ing.unit != "ml":
            amount = ing.amount * cfg.EXP_MAKER_FACTOR
        # usually show decimal places, up to 8, but if not ml is used clip decimal place
        threshold = 8 if ing.unit == "ml" else 0
        amount = int(round(amount, 1)) if amount >= threshold else round(amount, 1)
        if amount <= 0:
            continue
        unit = cfg.EXP_MAKER_UNIT if ing.unit == "ml" else ing.unit
        comment += f"\n~{amount} {unit} {ing.name}"

    return comment


def prepare_cocktail(
    cocktail: Cocktail,
    w: MainScreen | None = None,
    additional_message: str = "",
) -> tuple[PrepareResult, str]:
    """Prepare a Cocktail, if not already another one is in production and enough ingredients are available."""
    # Capture current waiter at preparation start (immune to logout during prep)
    waiter_nfc_id = shared.current_waiter_nfc_id
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    addon_data: dict[str, Any] = {"cocktail": cocktail}

    # only selects the positions where amount is not 0, if virgin this will remove alcohol from the recipe
    ingredients_machine = [x for x in cocktail.machineadds if x.amount > 0]
    _logger.info(f"Preparing {cocktail.adjusted_amount} ml {cocktail.display_name}")
    comment = _build_comment_maker(cocktail)

    # only use separator if we got both messages
    separator = "\n" if additional_message and comment else ""
    add_message = additional_message + separator + DH.cocktail_ready(comment)
    mc = MachineController()
    result = mc.make_cocktail(w, ingredients_machine, cocktail.display_name, finish_message=add_message)
    DBC = DatabaseCommander()
    # single ingredient got represented as a cocktail with one ingredient, but no id, skip recipe increment
    if cocktail.id != 0:
        DBC.increment_recipe_counter(cocktail.name, cocktail.is_virgin)

    # Set hand-add consumption before addon call so all data is available, always set hand add to recipe level
    cocktail.set_handadd_consumption()
    ADDONS.after_cocktail(addon_data)

    # only post if cocktail was made over 50%
    minimum_cocktail_progress = 0.5
    if result.completion_ratio >= minimum_cocktail_progress:
        SERVICE_HANDLER.post_team_data(shared.selected_team, cocktail.produced_volume, shared.team_member_name)
        SERVICE_HANDLER.post_cocktail_to_hook(cocktail, cocktail.produced_volume)

    # Persist all ingredient consumption
    consumption_names = [x.name for x in cocktail.adjusted_ingredients]
    consumption_amount = [round(x.consumption) for x in cocktail.adjusted_ingredients]
    DBC.set_multiple_ingredient_consumption(consumption_names, consumption_amount)

    if waiter_nfc_id is not None:
        DBC.log_waiter_cocktail(waiter_nfc_id, cocktail.id, cocktail.produced_volume, cocktail.is_virgin)
    if cfg.WAITER_LOGOUT_AFTER_COCKTAIL and cfg.waiter_mode_active:
        WaiterService().logout_waiter()

    if shared.cocktail_status.status == PrepareResult.CANCELED:
        DBC.save_event(EventType.COCKTAIL_CANCELED, f"{cocktail.display_name}")
        return PrepareResult.CANCELED, DH.get_translation("cocktail_canceled")

    DBC.save_event(EventType.COCKTAIL_PREPARATION, f"{cocktail.display_name}")
    shared.cocktail_status.status = PrepareResult.FINISHED
    return PrepareResult.FINISHED, add_message


def interrupt_cocktail() -> None:
    """Interrupts the cocktail preparation."""
    shared.cocktail_status.status = PrepareResult.CANCELED
    _logger.info("Canceling the cocktail over GUI!")


def validate_cocktail(cocktail: Cocktail) -> tuple[PrepareResult, str, Ingredient | None]:
    """Validate the cocktail.

    Returns the validator code | Error message (in case of addon).
    """
    # Check waiter mode: block if no registered waiter logged in
    if cfg.waiter_mode_active and shared.current_waiter is None:
        return PrepareResult.NO_WAITER_LOGGED_IN, DH.get_translation("no_waiter_logged_in"), None
    addon_data: dict[str, Any] = {"cocktail": cocktail}
    if shared.cocktail_status.status == PrepareResult.IN_PROGRESS:
        return PrepareResult.IN_PROGRESS, DH.cocktail_in_progress(), None
    empty_ingredient = None
    if cfg.MAKER_CHECK_BOTTLE:
        empty_ingredient = cocktail.enough_fill_level()
    if empty_ingredient is not None:
        msg = DH.not_enough_ingredient_volume(
            empty_ingredient.name,
            empty_ingredient.fill_level,
            empty_ingredient.amount,
        )
        if cfg.UI_MAKER_PASSWORD != 0 and cfg.UI_LOCKED_TABS[Tab.MAKER]:
            msg += f" \n\n{DH.get_translation('bottle_tab_locked')}"
        return PrepareResult.NOT_ENOUGH_INGREDIENTS, msg, empty_ingredient
    try:
        ADDONS.before_cocktail(addon_data)
    except RuntimeError as err:
        return PrepareResult.ADDON_ERROR, str(err), None

    return PrepareResult.VALIDATION_OK, "", None


def calibrate(bottle_number: int, amount: int) -> None:
    """Calibrate a bottle."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    display_name = f"{amount} ml volume, pump #{bottle_number}"
    ing = Ingredient(
        id=0,
        name="Calibration",
        alcohol=0,
        bottle_volume=1000,
        fill_level=1000,
        hand=False,
        pump_speed=100,
        amount=amount,
        bottle=bottle_number,
    )
    mc = MachineController()
    mc.make_cocktail(
        w=None,
        ingredient_list=[ing],
        recipe=display_name,
        is_cocktail=False,
        verbose=False,
    )


def prepare_ingredient(ingredient: Ingredient, w: MainScreen | None = None) -> None:
    """Prepare an ingredient."""
    shared.cocktail_status = CocktailStatus(status=PrepareResult.IN_PROGRESS)
    _logger.info(f"Spending {ingredient.amount} ml {ingredient.name}")
    mc = MachineController()
    mc.make_cocktail(w, [ingredient], ingredient.name, False)
    consumed_volume = round(ingredient.consumption)
    DBC = DatabaseCommander()
    DBC.increment_ingredient_consumption(ingredient.name, consumed_volume)
