from src.database_commander import DB_COMMANDER as DBC


class SaveHandler:
    def export_data(self) -> None:
        """Export the ingredient and recipe data to database, resets consumption."""
        DBC.export_ingredient_data()
        DBC.export_recipe_data()


SAVE_HANDLER = SaveHandler()
