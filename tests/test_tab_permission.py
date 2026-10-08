from src.api.models import TabPermission
from src.config.config_manager import Tab


def test_every_tab_maps_to_a_permission_flag() -> None:
    # the flag is looked up by the tab name, so a renamed field would only fail on a tab click
    for tab in Tab:
        assert TabPermission(**{tab.permission_key: True}).allows(tab)
