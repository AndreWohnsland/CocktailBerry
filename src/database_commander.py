from supporter import DatabaseHandler


class DatabaseCommander:
    def __init__(self):
        self.handler = DatabaseHandler()

    def get_ingredients(self, recipe_id):
        query = "SELECT Zutaten.Name, Zusammen.Menge, Zusammen.Hand FROM Zusammen INNER JOIN Zutaten ON Zusammen.Zutaten_ID = Zutaten.ID WHERE Zusammen.Rezept_ID = ?"
        return self.handler.query_database(query, (recipe_id,))

    def get_recipes(self):
        query = "SELECT ID, Name, Alkoholgehalt, Menge, Kommentar, Enabled, V_Alk, c_Alk, V_Com, c_Com FROM Rezepte"
        return self.handler.query_database(query)

    def build_recipe_object(self):
        recipe_object = {}
        recipe_data = self.get_recipes()
        for recipe in recipe_data:
            ingredient_data = self.get_ingredients(recipe[0])
            recipe_object[recipe[1]] = {
                "ID": recipe[0],
                "alcohollevel": recipe[2],
                "volume": recipe[3],
                "comment": recipe[4],
                "enabled": recipe[5],
                "volume_alcohol": recipe[6],
                "concentration_alcohol": recipe[7],
                "volume_comment": recipe[8],
                "concentration_comment": recipe[9],
                "ingredients": {a[0]: [a[1], a[2]] for a in ingredient_data},
            }
        return recipe_object
