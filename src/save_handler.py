from src.database_commander import DatabaseCommander


class SaveHandler:
    def export_data(self):
        """Export the ingredient and recipe data to database, resets consumption."""
        DBC = DatabaseCommander()
        DBC.export_ingredient_data()
        DBC.export_recipe_data()


SAVE_HANDLER = SaveHandler()
