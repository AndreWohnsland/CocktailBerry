from src.config.config_manager import CONFIG as cfg
from src.models import Cocktail, HandAddAssistItem


def _get_display_amount(amount: float, unit: str) -> int | float:
    display_amount = amount if unit == "ml" else amount * cfg.EXP_MAKER_FACTOR
    threshold = 8 if unit == "ml" else 0
    if display_amount >= threshold:
        return int(round(display_amount, 1))
    return round(display_amount, 1)


def build_hand_add_assist_items(cocktail: Cocktail) -> list[HandAddAssistItem]:
    """Build ordered hand-add items for assisted/manual post-dispense completion."""
    hand_adds = sorted(cocktail.handadds, key=lambda x: len(x.name) + len(x.unit), reverse=True)
    items: list[HandAddAssistItem] = []
    for index, ingredient in enumerate(hand_adds):
        if ingredient.amount <= 0:
            continue
        measurable = ingredient.unit == "ml"
        items.append(
            HandAddAssistItem(
                item_id=f"handadd-{index}",
                name=ingredient.name,
                display_amount=_get_display_amount(float(ingredient.amount), ingredient.unit),
                display_unit=cfg.EXP_MAKER_UNIT if measurable else ingredient.unit,
                measurable=measurable,
                target_weight_grams=float(ingredient.amount) if measurable else None,
            )
        )
    return items


def build_hand_add_comment(cocktail: Cocktail) -> str:
    """Build the classic completion comment for hand-add ingredients."""
    return "".join(
        f"\n~{item.display_amount} {item.display_unit} {item.name}" for item in build_hand_add_assist_items(cocktail)
    )


def should_use_hand_add_scale_assist(cocktail: Cocktail, has_scale: bool) -> bool:
    """Return whether the opt-in scale assisted hand-add flow should be used."""
    return cfg.MAKER_HANDADD_SCALE_ASSIST and has_scale and bool(build_hand_add_assist_items(cocktail))
