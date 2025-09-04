import datetime
from typing import Optional

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DbCocktailIngredient(Base):
    __tablename__ = "RecipeData"
    __table_args__ = (PrimaryKeyConstraint("Recipe_ID", "Ingredient_ID", name="recipe_ingredient_pk"),)
    cocktail_id: Mapped[int] = mapped_column(ForeignKey("Recipes.ID", ondelete="CASCADE"), name="Recipe_ID")
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("Ingredients.ID", ondelete="RESTRICT"), name="Ingredient_ID")
    amount: Mapped[int] = mapped_column(name="Amount", nullable=False)
    recipe_order: Mapped[int] = mapped_column(name="Recipe_Order", default=1)

    ingredient: Mapped["DbIngredient"] = relationship("DbIngredient", back_populates="cocktail_associations")
    cocktail: Mapped["DbRecipe"] = relationship("DbRecipe", back_populates="ingredient_associations")

    def __init__(self, cocktail_id: int, ingredient_id: int, amount: int, recipe_order: int = 1) -> None:
        self.cocktail_id = cocktail_id
        self.ingredient_id = ingredient_id
        self.amount = amount
        self.recipe_order = recipe_order


class DbIngredient(Base):
    __tablename__ = "Ingredients"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    name: Mapped[str] = mapped_column(unique=True, nullable=False, name="Name")
    alcohol: Mapped[int] = mapped_column(nullable=False, name="Alcohol")
    volume: Mapped[int] = mapped_column(name="Volume")
    consumption_lifetime: Mapped[int] = mapped_column(name="Consumption_lifetime")
    consumption: Mapped[int] = mapped_column(default=0, name="Consumption")
    cost_consumption_lifetime: Mapped[int] = mapped_column(name="Cost_consumption_lifetime")
    cost_consumption: Mapped[int] = mapped_column(default=0, name="Cost_consumption")
    fill_level: Mapped[int] = mapped_column(default=0, name="Fill_level")
    hand: Mapped[bool] = mapped_column(default=False, name="Hand")
    cost: Mapped[int] = mapped_column(default=0, name="Cost")
    unit: Mapped[str] = mapped_column(default="ml", name="Unit")
    pump_speed: Mapped[int] = mapped_column(default=100, name="Pump_speed")

    bottle: Mapped[Optional["DbBottle"]] = relationship("DbBottle", uselist=False, back_populates="ingredient")
    cocktail_associations: Mapped[list["DbCocktailIngredient"]] = relationship(
        "DbCocktailIngredient", back_populates="ingredient"
    )
    available: Mapped[Optional["DbAvailable"]] = relationship("DbAvailable", back_populates="ingredient", uselist=False)

    def __init__(
        self,
        name: str,
        alcohol: int,
        volume: int,
        consumption_lifetime: int = 0,
        consumption: int = 0,
        cost_consumption_lifetime: int = 0,
        cost_consumption: int = 0,
        fill_level: int = 0,
        hand: bool = False,
        slow: bool = False,
        cost: int = 0,
        unit: str = "ml",
        pump_speed: int = 100,
    ) -> None:
        self.name = name
        self.alcohol = alcohol
        self.volume = volume
        self.consumption_lifetime = consumption_lifetime
        self.consumption = consumption
        self.cost_consumption_lifetime = cost_consumption_lifetime
        self.cost_consumption = cost_consumption
        self.fill_level = fill_level
        self.hand = hand
        self.slow = slow
        self.cost = cost
        self.unit = unit
        self.pump_speed = pump_speed


class DbRecipe(Base):
    __tablename__ = "Recipes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    name: Mapped[str] = mapped_column(unique=True, nullable=False, name="Name")
    alcohol: Mapped[int] = mapped_column(nullable=False, name="Alcohol")
    amount: Mapped[int] = mapped_column(nullable=False, name="Amount")
    counter_lifetime: Mapped[int] = mapped_column(default=0, name="Counter_lifetime")
    counter_lifetime_virgin: Mapped[int] = mapped_column(default=0, name="Counter_lifetime_virgin")
    counter: Mapped[int] = mapped_column(default=0, name="Counter")
    counter_virgin: Mapped[int] = mapped_column(default=0, name="Counter_virgin")
    enabled: Mapped[bool] = mapped_column(default=True, name="Enabled")
    virgin: Mapped[bool] = mapped_column(default=False, name="Virgin")

    ingredient_associations: Mapped[list["DbCocktailIngredient"]] = relationship(
        "DbCocktailIngredient", back_populates="cocktail", cascade="all, delete-orphan"
    )

    def __init__(
        self,
        name: str,
        alcohol: int,
        amount: int,
        counter_lifetime: int = 0,
        counter_lifetime_virgin: int = 0,
        counter: int = 0,
        counter_virgin: int = 0,
        enabled: bool = True,
        virgin: bool = False,
    ) -> None:
        self.name = name
        self.alcohol = alcohol
        self.amount = amount
        self.counter_lifetime = counter_lifetime
        self.counter_lifetime_virgin = counter_lifetime_virgin
        self.counter = counter
        self.counter_virgin = counter_virgin
        self.enabled = enabled
        self.virgin = virgin


class DbBottle(Base):
    __tablename__ = "Bottles"
    number: Mapped[int] = mapped_column(primary_key=True, nullable=False, name="Bottle")
    id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Ingredients.ID", ondelete="RESTRICT"), nullable=True, name="ID"
    )

    ingredient: Mapped[Optional["DbIngredient"]] = relationship("DbIngredient", back_populates="bottle")

    def __init__(self, number: int, _id: Optional[int] = None) -> None:
        self.number = number
        self.id = _id


class DbAvailable(Base):
    __tablename__ = "Available"
    id: Mapped[int] = mapped_column(ForeignKey("Ingredients.ID"), primary_key=True, nullable=False, name="ID")

    ingredient: Mapped["DbIngredient"] = relationship("DbIngredient", back_populates="available")

    def __init__(self, _id: int) -> None:
        self.id = _id


class DbTeamdata(Base):
    __tablename__ = "Teamdata"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False, name="ID")
    payload: Mapped[str] = mapped_column(nullable=False, name="Payload")

    def __init__(self, payload: str) -> None:
        self.payload = payload


class DbCocktailExport(Base):
    __tablename__ = "CocktailExport"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    export_date: Mapped[datetime.date] = mapped_column(nullable=False, name="Export_Date", default=datetime.date.today)
    recipe_name: Mapped[str] = mapped_column(nullable=False, name="Recipe_Name")
    counter: Mapped[int] = mapped_column(nullable=False, name="Counter")
    counter_virgin: Mapped[int] = mapped_column(nullable=False, name="Counter_virgin")

    def __init__(
        self, recipe_name: str, counter: int, counter_virgin: int, export_date: Optional[datetime.date] = None
    ) -> None:
        self.recipe_name = recipe_name
        self.counter = counter
        self.counter_virgin = counter_virgin
        self.export_date = export_date or datetime.date.today()


class DbIngredientExport(Base):
    __tablename__ = "IngredientExport"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    export_date: Mapped[datetime.date] = mapped_column(nullable=False, name="Export_Date", default=datetime.date.today)
    ingredient_name: Mapped[str] = mapped_column(nullable=False, name="Ingredient_Name")
    consumption: Mapped[int] = mapped_column(nullable=False, name="Consumption")
    cost_consumption: Mapped[int] = mapped_column(nullable=False, name="Cost_Consumption")

    def __init__(
        self,
        ingredient_name: str,
        consumption: int,
        cost_consumption: int,
        export_date: Optional[datetime.date] = None,
    ) -> None:
        self.ingredient_name = ingredient_name
        self.consumption = consumption
        self.cost_consumption = cost_consumption
        self.export_date = export_date or datetime.date.today()


class DbResourceUsage(Base):
    __tablename__ = "ResourceUsage"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        nullable=False, name="Timestamp", default=datetime.datetime.now
    )
    cpu_usage: Mapped[float] = mapped_column(nullable=False, name="CPU_Usage")
    ram_usage: Mapped[float] = mapped_column(nullable=False, name="RAM_Usage")
    session: Mapped[int] = mapped_column(nullable=False, name="Session")

    def __init__(
        self,
        cpu_usage: float,
        ram_usage: float,
        session: int,
        timestamp: Optional[datetime.datetime] = None,
    ) -> None:
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.session = session
        self.timestamp = timestamp or datetime.datetime.now()
