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


class DbIngredient(Base):
    __tablename__ = "Ingredients"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    name: Mapped[str] = mapped_column(unique=True, nullable=False, name="Name")
    alcohol: Mapped[int] = mapped_column(nullable=False, name="Alcohol")
    volume: Mapped[int] = mapped_column(name="Volume")
    consumption_lifetime: Mapped[int] = mapped_column(name="Consumption_lifetime")
    consumption: Mapped[int] = mapped_column(default=0, name="Consumption")
    fill_level: Mapped[int] = mapped_column(default=0, name="Fill_level")
    hand: Mapped[bool] = mapped_column(default=False, name="Hand")
    slow: Mapped[bool] = mapped_column(default=False, name="Slow")
    cost: Mapped[int] = mapped_column(default=0, name="Cost")
    unit: Mapped[str] = mapped_column(default="ml", name="Unit")
    pump_speed: Mapped[int] = mapped_column(default=100, name="Pump_speed")

    bottle: Mapped[Optional["DbBottle"]] = relationship("DbBottle", uselist=False, back_populates="ingredient")
    cocktail_associations: Mapped[list["DbCocktailIngredient"]] = relationship(
        "DbCocktailIngredient", back_populates="ingredient"
    )
    available: Mapped[Optional["DbAvailable"]] = relationship("DbAvailable", back_populates="ingredient", uselist=False)


class DbRecipe(Base):
    __tablename__ = "Recipes"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, name="ID")
    name: Mapped[str] = mapped_column(unique=True, nullable=False, name="Name")
    alcohol: Mapped[int] = mapped_column(nullable=False, name="Alcohol")
    amount: Mapped[int] = mapped_column(nullable=False, name="Amount")
    counter_lifetime: Mapped[int] = mapped_column(default=0, name="Counter_lifetime")
    counter: Mapped[int] = mapped_column(default=0, name="Counter")
    enabled: Mapped[bool] = mapped_column(default=True, name="Enabled")
    virgin: Mapped[bool] = mapped_column(default=False, name="Virgin")

    ingredient_associations: Mapped[list["DbCocktailIngredient"]] = relationship(
        "DbCocktailIngredient", back_populates="cocktail", cascade="all, delete-orphan"
    )


class DbBottle(Base):
    __tablename__ = "Bottles"
    number: Mapped[int] = mapped_column(primary_key=True, nullable=False, name="Bottle")
    id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Ingredients.ID", ondelete="RESTRICT"), nullable=True, name="ID"
    )

    ingredient: Mapped[Optional["DbIngredient"]] = relationship("DbIngredient", back_populates="bottle")


class DbAvailable(Base):
    __tablename__ = "Available"
    id: Mapped[int] = mapped_column(ForeignKey("Ingredients.ID"), primary_key=True, nullable=False, name="ID")

    ingredient: Mapped["DbIngredient"] = relationship("DbIngredient", back_populates="available")


class DbTeamdata(Base):
    __tablename__ = "Teamdata"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False, name="ID")
    payload: Mapped[str] = mapped_column(nullable=False, name="Payload")
