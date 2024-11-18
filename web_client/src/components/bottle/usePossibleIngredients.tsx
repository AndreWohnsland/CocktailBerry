import { useState, useEffect } from 'react';
import { Bottle, Ingredient } from '../../types/models';
import { useIngredients } from '../../api/ingredients';

const usePossibleIngredients = (bottles: Bottle[]) => {
  const { data: ingredients, error: ingredientsError, isLoading: ingredientsLoading } = useIngredients();
  const [possibleIngredients, setPossibleIngredients] = useState<Ingredient[]>([]);

  useEffect(() => {
    if (ingredients) {
      const usedIngredientIds = bottles.map((bottle) => bottle.ingredient?.id).filter((id) => id !== undefined);
      const availableIngredients = ingredients.filter((ingredient) => !usedIngredientIds.includes(ingredient.id));
      setPossibleIngredients(availableIngredients);
    }
  }, [ingredients, bottles]);

  const updatePossibleIngredients = (oldIngredientId: number | undefined, newIngredientId: number | undefined) => {
    setPossibleIngredients((prev) => {
      let updated = [...prev];
      if (oldIngredientId !== undefined) {
        const oldIngredient = ingredients?.find((ingredient) => ingredient.id === oldIngredientId);
        if (oldIngredient) {
          updated.push(oldIngredient);
        }
      }
      if (newIngredientId !== undefined) {
        updated = updated.filter((ingredient) => ingredient.id !== newIngredientId);
      }
      return updated;
    });
  };

  return { possibleIngredients, updatePossibleIngredients, ingredientsLoading, ingredientsError };
};

export default usePossibleIngredients;
