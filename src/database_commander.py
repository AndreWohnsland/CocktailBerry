from __future__ import annotations

import datetime
import shutil
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from statistics import mean, median
from typing import TYPE_CHECKING, Any, Literal

import sqlalchemy
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from src.db_models import (
    Base,
    DbAvailable,
    DbBottle,
    DbCocktailExport,
    DbCocktailIngredient,
    DbIngredient,
    DbIngredientExport,
    DbRecipe,
    DbResourceUsage,
    DbTeamdata,
)
from src.dialog_handler import DialogHandler
from src.filepath import DATABASE_PATH, DEFAULT_DATABASE_PATH, HOME_PATH
from src.logger_handler import LoggerHandler
from src.models import Cocktail, ConsumeData, Ingredient, ResourceInfo, ResourceStats
from src.utils import time_print

if TYPE_CHECKING:
    from src.dialog_handler import allowed_keys

_logger = LoggerHandler("database_module")

VIRGIN_NAME_TEMPLATE = "(V) {}"


class DatabaseTransactionError(Exception):
    """Raises an error if something will not work in the database with the given command.

    The reason will be contained in the message with the corresponding translation key.
    """

    def __init__(self, translation_key: allowed_keys, language_args: dict | None = None) -> None:
        DH = DialogHandler()
        self.language_args = language_args if language_args is not None else {}
        messsage = DH.get_translation(translation_key, **self.language_args)
        super().__init__(messsage)
        self.translation_key = translation_key


class ElementNotFoundError(DatabaseTransactionError):
    """Informs that the element was not found in the database."""

    def __init__(self, element_name: str) -> None:
        super().__init__("element_not_found", {"element_name": element_name})


class ElementAlreadyExistsError(DatabaseTransactionError):
    """Informs that the element already is in the db."""

    def __init__(self, element_name: str) -> None:
        super().__init__("element_already_exists", {"element_name": element_name})


class DatabaseCommander:
    """Commander Class to execute queries and return the results as lists."""

    database_path = DATABASE_PATH
    database_path_default = DEFAULT_DATABASE_PATH

    def __init__(self, use_default: bool = False, db_url: str | None = None) -> None:
        if not self.database_path.exists():
            time_print("Copying default database for maker usage")
            self.copy_default_database()
        if db_url is None:
            self.db_url = f"sqlite:///{self.database_path_default if use_default else self.database_path}"
        else:
            self.db_url = db_url
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))

    def __del__(self) -> None:
        """Close the session when the object is deleted."""
        self.Session.remove()
        self.engine.dispose()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def copy_default_database(self) -> None:
        """Create a local copy of the database."""
        shutil.copy(self.database_path_default, self.database_path)

    def copy_default_data_to_current_db(self) -> None:
        default_engine = create_engine(f"sqlite:///{self.database_path_default}", echo=False)
        with default_engine.connect() as conn:
            for table in Base.metadata.sorted_tables:
                data = conn.execute(table.select()).fetchall()
                if not data:
                    continue
                # Convert each row to a dictionary
                data_dicts = [dict(row._mapping) for row in data]
                with self.session_scope() as session:
                    session.execute(table.insert(), data_dicts)

    def create_backup(self) -> None:
        """Create a backup locally in the same folder, used before migrations."""
        dtime = datetime.datetime.now()
        suffix = dtime.strftime("%Y-%m-%d-%H-%M-%S")
        full_backup_name = f"{DATABASE_PATH.stem}_backup-{suffix}.db"
        backup_path = HOME_PATH / full_backup_name
        _logger.log_event("INFO", f"Creating backup with name: {full_backup_name}")
        _logger.log_event("INFO", f"Use this to overwrite: {DATABASE_PATH.name} in case of failure")
        shutil.copy(DATABASE_PATH, backup_path)

    def _map_cocktail(self, recipe: DbRecipe) -> Cocktail:
        """Map the Recipe database class to the Cocktail dataclass."""
        return Cocktail(
            id=recipe.id,
            name=recipe.name,
            alcohol=recipe.alcohol,
            amount=recipe.amount,
            price=recipe.price,
            enabled=recipe.enabled,
            virgin_available=recipe.virgin,
            ingredients=[self._map_cocktail_ingredient(x) for x in recipe.ingredient_associations],
        )

    def _map_cocktail_ingredient(self, data: DbCocktailIngredient) -> Ingredient:
        """Map the CocktailIngredient database class to the Ingredient dataclass."""
        return Ingredient(
            id=data.ingredient.id,
            name=data.ingredient.name,
            alcohol=data.ingredient.alcohol,
            bottle_volume=data.ingredient.volume,
            fill_level=data.ingredient.fill_level,
            hand=data.ingredient.hand,
            pump_speed=data.ingredient.pump_speed,
            amount=data.amount,
            bottle=data.ingredient.bottle.number if data.ingredient.bottle else None,
            cost=data.ingredient.cost,
            recipe_order=data.recipe_order,
            unit=data.ingredient.unit,
        )

    def _map_ingredient(self, data: DbIngredient) -> Ingredient:
        """Map the Ingredient database class to the Ingredient dataclass."""
        return Ingredient(
            id=data.id,
            name=data.name,
            alcohol=data.alcohol,
            bottle_volume=data.volume,
            fill_level=data.fill_level,
            hand=data.hand,
            pump_speed=data.pump_speed,
            bottle=data.bottle.number if data.bottle else None,
            cost=data.cost,
            unit=data.unit,
        )

    def _empty_ingredient(self, bottle: int) -> Ingredient:
        """Return an empty ingredient dataclass."""
        return Ingredient(
            id=0, name="", alcohol=0, bottle_volume=0, fill_level=0, hand=False, pump_speed=0, bottle=bottle
        )

    def get_cocktail(self, search: str | int) -> Cocktail | None:
        """Get all needed data for the cocktail from ID or name."""
        with self.session_scope() as session:
            if isinstance(search, str):
                recipe = session.query(DbRecipe).filter(DbRecipe.name == search).one_or_none()
            else:
                recipe = session.query(DbRecipe).filter(DbRecipe.id == search).one_or_none()
            if recipe is None:
                return None
            return self._map_cocktail(recipe)

    def _get_db_cocktails(
        self, session: Session, status: Literal["all", "enabled", "disabled"] = "all"
    ) -> list[DbRecipe]:
        """Get all cocktails from the database."""
        stmt = session.query(DbRecipe)
        if status == "enabled":
            stmt = stmt.filter(DbRecipe.enabled.is_(True))
        elif status == "disabled":
            stmt = stmt.filter(DbRecipe.enabled.is_(False))
        return stmt.all()

    def get_all_cocktails(self, status: Literal["all", "enabled", "disabled"] = "all") -> list[Cocktail]:
        """Build a list of all cocktails, option to filter by enabled status."""
        with self.session_scope() as session:
            cocktails = self._get_db_cocktails(session, status)
            return [self._map_cocktail(x) for x in cocktails]

    def get_possible_cocktails(self, max_hand_ingredients: int) -> list[Cocktail]:
        """Return a list of currently possible cocktails with the current bottles."""
        all_cocktails = self.get_all_cocktails(status="enabled")
        handadds_ids = self.get_available_ids()
        return [x for x in all_cocktails if x.is_possible(handadds_ids, max_hand_ingredients)]

    def get_ingredient_names_at_bottles(self) -> list[str]:
        """Return ingredient name for all bottles, including empty ones as empty strings."""
        data = self.get_ingredients_at_bottles()
        return [x.name for x in data]

    def get_ingredient_at_bottle(self, bottle: int) -> Ingredient | None:
        """Return ingredient name for all bottles."""
        with self.session_scope() as session:
            data = session.query(DbIngredient).filter(DbIngredient.bottle.has(number=bottle)).one_or_none()
            if data is None:
                return None
            return self._map_ingredient(data)

    def get_ingredients_at_bottles(self) -> list[Ingredient]:
        """Return ingredient name for all bottles."""
        with self.session_scope() as session:
            data = (
                session.query(DbBottle, DbIngredient)
                .outerjoin(DbIngredient, DbBottle.id == DbIngredient.id)
                .order_by(DbBottle.number)
                .all()
            )
            result = []
            for bottle, ingredient in data:
                if ingredient is None:
                    result.append(self._empty_ingredient(bottle.number))
                else:
                    result.append(self._map_ingredient(ingredient))
            return result

    def get_bottle_fill_levels(self) -> list[int]:
        """Return percentage of fill level, limited to [0, 100]."""
        with self.session_scope() as session:
            data = session.query(DbBottle).order_by(DbBottle.number).all()
            return [
                round(min(max(x.ingredient.fill_level / x.ingredient.volume * 100, 0), 100))
                if x.ingredient is not None
                else 0
                for x in data
            ]

    def get_ingredient(self, search: str | int) -> Ingredient | None:
        """Get all needed data for the ingredient from ID or name."""
        with self.session_scope() as session:
            if isinstance(search, str):
                ingredient = session.query(DbIngredient).filter(DbIngredient.name == search).one_or_none()
            else:
                ingredient = session.query(DbIngredient).filter(DbIngredient.id == search).one_or_none()
            if ingredient is None:
                return None
            return self._map_ingredient(ingredient)

    def _get_all_db_ingredients(
        self, session: Session, get_machine: bool = True, get_hand: bool = True
    ) -> list[DbIngredient]:
        """Get all ingredients from the database."""
        if not get_machine and not get_hand:
            return []
        stmt = session.query(DbIngredient)
        if not get_machine:
            stmt = stmt.filter(DbIngredient.hand.is_(True))
        elif not get_hand:
            stmt = stmt.filter(DbIngredient.hand.is_(False))
        return stmt.all()

    def get_all_ingredients(self, get_machine: bool = True, get_hand: bool = True) -> list[Ingredient]:
        """Build a list of all ingredients, option to filter by add status."""
        with self.session_scope() as session:
            ingredients = self._get_all_db_ingredients(session, get_machine, get_hand)
            return [self._map_ingredient(x) for x in ingredients]

    def get_bottle_usage(self, ingredient_id: int) -> bool:
        """Return if the ingredient id is currently used at a bottle."""
        with self.session_scope() as session:
            count = session.query(DbBottle).where(DbBottle.id == ingredient_id).count()
            return count != 0

    def get_recipe_usage_list(self, ingredient_id: int) -> list[str]:
        """Get all the recipe names the ingredient is used in."""
        with self.session_scope() as session:
            data = (
                session.query(DbRecipe.name)
                .join(DbCocktailIngredient)
                .filter(DbCocktailIngredient.ingredient_id == ingredient_id)
                .all()
            )
        return [recipe[0] for recipe in data]

    def get_consumption_data_lists_recipes(self) -> list[list[Any]]:
        """Return the recipe consumption data ready to export."""
        with self.session_scope() as session:
            cocktails = self._get_db_cocktails(session)
            return self._convert_consumption_data(
                [x.name for x in cocktails] + [VIRGIN_NAME_TEMPLATE.format(x.name) for x in cocktails],
                [x.counter for x in cocktails] + [x.counter_virgin for x in cocktails],
                [x.counter_lifetime for x in cocktails] + [x.counter_lifetime_virgin for x in cocktails],
            )

    def get_consumption_data_lists_ingredients(self) -> list[list[Any]]:
        """Return the ingredient consumption data ready to export."""
        with self.session_scope() as session:
            ingredients = self._get_all_db_ingredients(session)
            return self._convert_consumption_data(
                [x.name for x in ingredients],
                [x.consumption for x in ingredients],
                [x.consumption_lifetime for x in ingredients],
            )

    def get_cost_data_lists_ingredients(self) -> list[list[Any]]:
        """Return the ingredient cost data ready to export."""
        with self.session_scope() as session:
            ingredients = self._get_all_db_ingredients(session)
            return self._convert_consumption_data(
                [x.name for x in ingredients],
                [x.cost_consumption for x in ingredients],
                [x.cost_consumption_lifetime for x in ingredients],
            )

    def _convert_consumption_data(
        self, headers: list[str], resettable: list[int], lifetime: list[int]
    ) -> list[list[Any]]:
        """Convert the data from the db cursor into needed csv format."""
        return [["date", *headers], [datetime.date.today(), *resettable], ["lifetime", *lifetime]]

    def get_available_ingredient_names(self) -> list[str]:
        """Get the names for the available ingredients."""
        with self.session_scope() as session:
            data = session.query(DbIngredient.name).join(DbAvailable, DbIngredient.id == DbAvailable.id).all()
            return [x[0] for x in data]

    def get_available_ids(self) -> list[int]:
        """Return a list of the IDs of all available defined ingredients."""
        with self.session_scope() as session:
            data = session.query(DbAvailable.id).all()
            return [x[0] for x in data]

    # set (update) commands
    def set_bottle_order(self, ingredient_names: list[str] | list[int]) -> None:
        """Set bottles to the given list of bottles, need all bottles."""
        for bottle, ingredient in enumerate(ingredient_names, start=1):
            self.set_bottle_at_slot(ingredient, bottle)  # type: ignore[arg-type]

    def set_bottle_at_slot(self, ingredient: str | int, bottle_number: int) -> None:
        """Set the bottle at the given slot."""
        with self.session_scope() as session:
            if isinstance(ingredient, int):
                ingredient_id: int | None = ingredient
            else:
                ingredient_obj = session.query(DbIngredient).filter(DbIngredient.name == ingredient).one_or_none()
                ingredient_id = None if ingredient_obj is None else ingredient_obj.id

            bottle = session.query(DbBottle).filter(DbBottle.number == bottle_number).one_or_none()
            # if the bottle is none, we need to create a new bottle
            if bottle is None:
                bottle = DbBottle(number=bottle_number, _id=ingredient_id)
                session.add(bottle)
            bottle.id = ingredient_id

    def set_bottle_volumelevel_to_max(self, bottle_number_list: list[int]) -> None:
        """Set the each i-th bottle to max level if arg is true."""
        with self.session_scope() as session:
            for bottle_number in bottle_number_list:
                bottle = session.query(DbBottle).filter(DbBottle.number == bottle_number).one_or_none()
                if bottle and bottle.ingredient:
                    bottle.ingredient.fill_level = bottle.ingredient.volume

    def set_ingredient_data(
        self,
        ingredient_name: str,
        alcohol_level: int,
        volume: int,
        new_level: int,
        only_hand: bool,
        pump_speed: int,
        ingredient_id: int,
        cost: int,
        unit: str,
    ) -> None:
        """Update the given ingredient id to new properties."""
        with self.session_scope() as session:
            ingredient = session.query(DbIngredient).filter(DbIngredient.id == ingredient_id).one_or_none()
            if ingredient is None:
                raise ElementNotFoundError(f"Ingredient ID {ingredient_id}")

            ingredient.name = ingredient_name
            ingredient.alcohol = alcohol_level
            ingredient.volume = volume
            ingredient.fill_level = new_level
            ingredient.hand = only_hand
            ingredient.pump_speed = pump_speed
            ingredient.cost = cost
            ingredient.unit = unit

    def increment_recipe_counter(self, recipe_name: str, virgin: bool) -> None:
        """Increase the recipe counter by one of given recipe name."""
        with self.session_scope() as session:
            recipe = session.query(DbRecipe).filter(DbRecipe.name == recipe_name).one_or_none()
            if recipe is None:
                raise ElementNotFoundError(f"Recipe with name {recipe_name} not found")

            if virgin:
                recipe.counter_lifetime_virgin += 1
                recipe.counter_virgin += 1
            else:
                recipe.counter_lifetime += 1
                recipe.counter += 1

    def increment_ingredient_consumption(self, ingredient_name: str, ingredient_consumption: int) -> None:
        """Increase the consumption of given ingredient name by a given amount."""
        with self.session_scope() as session:
            ingredient = session.query(DbIngredient).filter(DbIngredient.name == ingredient_name).one_or_none()
            if ingredient is None:
                raise ElementNotFoundError(ingredient_name)

            ingredient.consumption_lifetime += ingredient_consumption
            ingredient.consumption += ingredient_consumption
            # update fill level, limit to 0
            ingredient.fill_level -= ingredient_consumption
            ingredient.fill_level = max(ingredient.fill_level, 0)
            # update the cost consumption
            occurred_cost = int(round(ingredient.cost / ingredient.volume * ingredient_consumption, 0))
            ingredient.cost_consumption += occurred_cost
            ingredient.cost_consumption_lifetime += occurred_cost

    def set_multiple_ingredient_consumption(
        self,
        ingredient_name_list: list[str],
        ingredient_consumption_list: list[int],
    ) -> None:
        """Increase multiple ingredients by the according given consumption."""
        for ingredient_name, ingredient_consumption in zip(ingredient_name_list, ingredient_consumption_list):
            self.increment_ingredient_consumption(ingredient_name, ingredient_consumption)

    def set_all_recipes_enabled(self) -> None:
        """Enable all recipes."""
        with self.session_scope() as session:
            session.query(DbRecipe).update({DbRecipe.enabled: True})

    def set_recipe(
        self,
        recipe_id: int,
        name: str,
        alcohol_level: int,
        volume: int,
        price: float,
        enabled: bool,
        virgin: bool,
        ingredient_data: list[tuple[int, int, int]],
    ) -> Cocktail:
        """Update the given recipe id to new properties."""
        self.delete_recipe_ingredient_data(recipe_id)
        with self.session_scope() as session:
            recipe = session.query(DbRecipe).filter(DbRecipe.id == recipe_id).one_or_none()
            if recipe is None:
                raise ElementNotFoundError(f"Recipe ID {recipe_id} not found")

            recipe.name = name
            recipe.alcohol = alcohol_level
            recipe.amount = volume
            recipe.enabled = enabled
            recipe.virgin = virgin
            recipe.price = price

            for _id, amount, order in ingredient_data:
                self.insert_recipe_data(recipe_id, _id, amount, order)
            session.commit()
            return self.get_cocktail(recipe_id)  # type: ignore

    def set_ingredient_level_to_value(self, ingredient_id: int, value: int) -> None:
        """Set the given ingredient id to a defined level."""
        with self.session_scope() as session:
            ingredient = session.query(DbIngredient).filter(DbIngredient.id == ingredient_id).one_or_none()
            if ingredient is None:
                raise ElementNotFoundError(f"Ingredient ID {ingredient_id}")
            ingredient.fill_level = value

    # insert commands
    def insert_new_ingredient(
        self,
        ingredient_name: str,
        alcohol_level: int,
        volume: int,
        only_hand: bool,
        pump_speed: int,
        cost: int,
        unit: str,
    ) -> None:
        """Insert a new ingredient into the database."""
        new_ingredient = DbIngredient(
            name=ingredient_name,
            alcohol=alcohol_level,
            volume=volume,
            consumption_lifetime=0,
            consumption=0,
            fill_level=0,
            hand=only_hand,
            pump_speed=pump_speed,
            cost=cost,
            unit=unit,
        )
        with self.session_scope() as session:
            try:
                session.add(new_ingredient)
                session.commit()
            except Exception as e:
                session.rollback()
                if isinstance(e, (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError)):  # type: ignore
                    raise ElementAlreadyExistsError(ingredient_name)
                raise e

    def insert_new_recipe(
        self,
        name: str,
        alcohol_level: int,
        volume: int,
        price: float,
        enabled: bool,
        virgin: bool,
        ingredient_data: list[tuple[int, int, int]],
    ) -> Cocktail:
        """Insert a new recipe into the database."""
        new_recipe = DbRecipe(
            name=name,
            alcohol=alcohol_level,
            amount=volume,
            price=price,
            counter_lifetime=0,
            counter=0,
            enabled=enabled,
            virgin=virgin,
        )
        with self.session_scope() as session:
            try:
                session.add(new_recipe)
                session.commit()
            except Exception as e:
                session.rollback()
                if isinstance(e, (sqlite3.IntegrityError, sqlalchemy.exc.IntegrityError)):  # type: ignore
                    raise ElementAlreadyExistsError(name)
                raise e

            cocktail: Cocktail = self.get_cocktail(name)  # type: ignore
            for _id, amount, order in ingredient_data:
                self.insert_recipe_data(cocktail.id, _id, amount, order)
            return self.get_cocktail(name)  # type: ignore

    def insert_recipe_data(self, recipe_id: int, ingredient_id: int, ingredient_volume: int, order_number: int) -> None:
        """Insert given data into the recipe_data table."""
        with self.session_scope() as session:
            new_cocktail_ingredient = DbCocktailIngredient(
                cocktail_id=recipe_id,
                ingredient_id=ingredient_id,
                amount=ingredient_volume,
                recipe_order=order_number,
            )
            session.add(new_cocktail_ingredient)

    def insert_multiple_existing_handadd_ingredients(self, ingredient_list: list[str] | list[int]) -> None:
        """Insert the IDS of the given ingredient list into the available table."""
        if not ingredient_list:
            return
        with self.session_scope() as session:
            if isinstance(ingredient_list[0], str):
                data = session.query(DbIngredient.id).filter(DbIngredient.name.in_(ingredient_list)).all()
                ingredient_id: list[int] = [x[0] for x in data]
            else:
                ingredient_id = ingredient_list  # type: ignore
            for _id in ingredient_id:
                session.add(DbAvailable(_id=_id))

    # delete
    def delete_ingredient(self, ingredient_id: int) -> None:
        """Delete an ingredient by id."""
        if self.get_bottle_usage(ingredient_id):
            raise DatabaseTransactionError("ingredient_still_at_bottle")
        if ingredient_id in self.get_available_ids():
            raise DatabaseTransactionError("ingredient_still_in_available")
        recipe_list = self.get_recipe_usage_list(ingredient_id)
        if recipe_list:
            recipe_string = ", ".join(recipe_list)
            raise DatabaseTransactionError("ingredient_still_at_recipe", {"recipe_string": recipe_string})
        with self.session_scope() as session:
            ingredient = session.query(DbIngredient).filter(DbIngredient.id == ingredient_id).one_or_none()
            if ingredient is None:
                raise ElementNotFoundError(f"Ingredient ID {ingredient_id} not found")
            session.delete(ingredient)

    def delete_recipe(self, recipe_name: str | int) -> None:
        """Delete the given recipe by name and all according ingredient_data."""
        with self.session_scope() as session:
            if isinstance(recipe_name, str):
                recipe = session.query(DbRecipe).filter(DbRecipe.name == recipe_name).one_or_none()
            else:
                recipe = session.query(DbRecipe).filter(DbRecipe.id == recipe_name).one_or_none()
            if recipe is None:
                raise ElementNotFoundError(f"Recipe {recipe_name} not found")
            session.delete(recipe)

    def delete_recipe_ingredient_data(self, recipe_id: int) -> None:
        """Delete ingredient_data by given ID."""
        with self.session_scope() as session:
            session.query(DbCocktailIngredient).filter(DbCocktailIngredient.cocktail_id == recipe_id).delete()

    def delete_existing_handadd_ingredient(self) -> None:
        """Delete all ingredient in the available table."""
        with self.session_scope() as session:
            session.query(DbAvailable).delete()

    def delete_database_data(self) -> None:
        """Remove all the data from the db for a local reset."""
        with self.session_scope() as session:
            session.query(DbAvailable).delete()
            session.query(DbBottle).update({DbBottle.id: None})
            session.query(DbCocktailIngredient).delete()
            session.query(DbRecipe).delete()
            session.query(DbIngredient).delete()

    def save_failed_teamdata(self, payload: str) -> None:
        """Save the failed payload into the db to buffer."""
        with self.session_scope() as session:
            new_teamdata = DbTeamdata(payload=payload)
            session.add(new_teamdata)

    def get_failed_teamdata(self) -> tuple[int, str] | None:
        """Return one failed teamdata payload."""
        with self.session_scope() as session:
            data = session.query(DbTeamdata).order_by(DbTeamdata.id.asc()).first()
            if data:
                return (data.id, data.payload)
            return None

    def delete_failed_teamdata(self, data_id: int) -> None:
        """Delete the given teamdata by id."""
        with self.session_scope() as session:
            teamdata = session.query(DbTeamdata).filter(DbTeamdata.id == data_id).one_or_none()
            if teamdata is None:
                raise ElementNotFoundError(f"Teamdata ID {data_id} not found")
            session.delete(teamdata)

    def export_recipe_data(self) -> None:
        """Save the recipe consumption data to the database and reset counters."""
        today = datetime.date.today()
        with self.session_scope() as session:
            recipes = self._get_db_cocktails(session)
            for recipe in recipes:
                if recipe.counter + recipe.counter_virgin == 0:
                    continue
                existing_export = (
                    session.query(DbCocktailExport)
                    .filter(DbCocktailExport.export_date == today)
                    .filter(DbCocktailExport.recipe_name == recipe.name)
                    .one_or_none()
                )
                if existing_export:
                    existing_export.counter += recipe.counter
                    existing_export.counter_virgin += recipe.counter_virgin
                else:
                    session.add(DbCocktailExport(recipe.name, recipe.counter, recipe.counter_virgin))

            # Reset counters after recording
            session.query(DbRecipe).update({DbRecipe.counter: 0, DbRecipe.counter_virgin: 0})
        _logger.log_event("INFO", "Recipe consumption data was saved to database")

    def export_ingredient_data(self) -> None:
        """Save the ingredient consumption and cost data to the database and reset counters."""
        today = datetime.date.today()
        with self.session_scope() as session:
            ingredients = self._get_all_db_ingredients(session)
            for ingredient in ingredients:
                if ingredient.consumption == 0:
                    continue
                existing_export = (
                    session.query(DbIngredientExport)
                    .filter(DbIngredientExport.export_date == today)
                    .filter(DbIngredientExport.ingredient_name == ingredient.name)
                    .one_or_none()
                )
                if existing_export:
                    existing_export.consumption += ingredient.consumption
                    existing_export.cost_consumption += ingredient.cost_consumption
                else:
                    session.add(
                        DbIngredientExport(ingredient.name, ingredient.consumption, ingredient.cost_consumption)
                    )

            # Reset consumption after recording
            session.query(DbIngredient).update({DbIngredient.consumption: 0, DbIngredient.cost_consumption: 0})
        _logger.log_event("INFO", "Ingredient consumption data was saved to database")

    def get_export_dates(self) -> list[str]:
        """Get all available export dates from the database."""
        with self.session_scope() as session:
            recipe_dates = session.query(DbCocktailExport.export_date).distinct().all()
            all_dates = {date[0].strftime("%Y-%m-%d") for date in recipe_dates}
            return sorted(all_dates)

    def get_export_data(self) -> dict[str, ConsumeData]:
        """Get all export data from the database."""
        with self.session_scope() as session:
            recipe_exports = session.query(DbCocktailExport).all()
            ingredient_exports = session.query(DbIngredientExport).all()
            date_grouped_data: dict[str, dict[str, dict[str, int]]] = {}

            for r_export in recipe_exports:
                date_str = r_export.export_date.strftime("%Y-%m-%d")
                if date_str not in date_grouped_data:
                    date_grouped_data[date_str] = {"recipes": {}, "ingredients": {}, "cost": {}}
                if r_export.counter > 0:
                    date_grouped_data[date_str]["recipes"][r_export.recipe_name] = r_export.counter
                if r_export.counter_virgin > 0:
                    name = VIRGIN_NAME_TEMPLATE.format(r_export.recipe_name)
                    date_grouped_data[date_str]["recipes"][name] = r_export.counter_virgin

            for i_export in ingredient_exports:
                date_str = i_export.export_date.strftime("%Y-%m-%d")
                if date_str not in date_grouped_data:
                    date_grouped_data[date_str] = {"recipes": {}, "ingredients": {}, "cost": {}}
                date_grouped_data[date_str]["ingredients"][i_export.ingredient_name] = i_export.consumption
                if i_export.cost_consumption > 0:
                    date_grouped_data[date_str]["cost"][i_export.ingredient_name] = i_export.cost_consumption

            return {
                date_str: ConsumeData(recipes=data["recipes"], ingredients=data["ingredients"], cost=data["cost"])
                for date_str, data in date_grouped_data.items()
            }

    def save_resource_usage(
        self, cpu_usage: float, ram_usage: float, session_number: int, timestamp: datetime.datetime | None = None
    ) -> None:
        """Save the resource usage to the database."""
        with self.session_scope() as session:
            usage = DbResourceUsage(
                cpu_usage=cpu_usage,
                ram_usage=ram_usage,
                session=session_number,
                timestamp=timestamp,
            )
            session.add(usage)
            session.commit()

    def get_resource_stats(self, session_number: int) -> ResourceStats:
        """Get the resource usage for a specific session."""
        with self.session_scope() as session_scope:
            query = (
                session_scope.query(DbResourceUsage)
                .filter(DbResourceUsage.session == session_number)
                .order_by(DbResourceUsage.timestamp)
            )
            data = query.all()
            if not data:
                return ResourceStats(0, 0, 0, 0, 0, 0, 0, 0, 0, [], [])
            cpu_values = [d.cpu_usage for d in data]
            ram_values = [d.ram_usage for d in data]
            return ResourceStats(
                min_cpu=min(cpu_values),
                max_cpu=max(cpu_values),
                mean_cpu=round(mean(cpu_values), 1),
                median_cpu=median(cpu_values),
                min_ram=min(ram_values),
                max_ram=max(ram_values),
                mean_ram=round(mean(ram_values), 1),
                median_ram=median(ram_values),
                samples=len(data),
                raw_cpu=cpu_values,
                raw_ram=ram_values,
            )

    def get_resource_session_numbers(self) -> list[ResourceInfo]:
        """Get all session numbers with their minimum timestamp from the database."""
        with self.session_scope() as session:
            data = (
                session.query(DbResourceUsage.session, sqlalchemy.func.min(DbResourceUsage.timestamp))
                .group_by(DbResourceUsage.session)
                .all()
            )
            return sorted(
                [ResourceInfo(row[0], row[1].strftime("%Y-%m-%d %H:%M") if row[1] else "") for row in data],
                key=lambda x: x.session_id,
            )

    def get_highest_session_number(self) -> int:
        """Get the highest session number from the database, zero if there is no data."""
        with self.session_scope() as session:
            data = session.query(DbResourceUsage.session).order_by(DbResourceUsage.session.desc()).first()
            return data[0] if data else 0

    def get_most_used_ingredient_ids(self, k: int | None = None) -> set[int]:
        with self.session_scope() as session:
            count_query = (
                session.query(DbCocktailIngredient.ingredient_id)
                .join(DbRecipe, DbCocktailIngredient.cocktail_id == DbRecipe.id)
                .filter(DbRecipe.enabled.is_(True))
                .group_by(DbCocktailIngredient.ingredient_id)
                .order_by(func.count(DbCocktailIngredient.cocktail_id).desc())
            )
            if k and k > 0:
                count_query = count_query.limit(k)
            top_pairs = count_query.all()
            top_ing_ids: list[int] = [row[0] for row in top_pairs]

        return set(top_ing_ids)


DB_COMMANDER = DatabaseCommander()
