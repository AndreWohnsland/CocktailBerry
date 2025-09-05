import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { RxCrossCircled } from 'react-icons/rx';
import { useCocktails } from '../../api/cocktails.ts';
import type { CocktailIngredient } from '../../types/models.ts';
import Accordion from '../common/Accordion.tsx';

type CocktailIngredientWithRecipes = CocktailIngredient & { recipes: { id: number; name: string }[] };

function RecipeCalculator() {
  const { t } = useTranslation();
  const [selectedCocktails, setSelectedCocktails] = useState<number[]>([]);
  const { data: cocktails, isLoading } = useCocktails(false, 0, false);

  const handleCocktailSelect = (id: number) => {
    setSelectedCocktails((prev) =>
      prev.includes(id) ? prev.filter((cocktailId) => cocktailId !== id) : [...prev, id],
    );
  };

  const handleRemoveCocktail = (id: number) => {
    setSelectedCocktails((prev) => prev.filter((cocktailId) => cocktailId !== id));
  };

  const neededIngredients = useMemo(() => {
    if (!cocktails) return [];
    const selected = cocktails.filter((c) => selectedCocktails.includes(c.id));
    const ingredients = new Map<number, CocktailIngredientWithRecipes>();

    for (const cocktail of selected) {
      for (const ingredient of cocktail.ingredients) {
        if (ingredients.has(ingredient.id)) {
          ingredients.get(ingredient.id)?.recipes.push({ id: cocktail.id, name: cocktail.name });
        } else {
          ingredients.set(ingredient.id, { ...ingredient, recipes: [{ id: cocktail.id, name: cocktail.name }] });
        }
      }
    }
    return [...ingredients.values()].sort((a, b) => b.recipes.length - a.recipes.length);
  }, [cocktails, selectedCocktails]);

  return (
    <div className='max-w-7xl w-full px-1 flex flex-col h-full'>
      <h1 className='text-center text-2xl font-bold text-secondary mb-4'>{t('recipeCalculation.title')}</h1>
      <div className='flex-grow flex flex-col sm:flex-row justify-start items-start w-full h-full sm:h-[70vh] h-md:mb-6 mb-2'>
        <div className='w-full sm:w-1/2 h-full flex flex-col'>
          <h2 className='font-bold mb-2 text-center text-xl text-secondary'>{t('header.cocktails')}</h2>
          {isLoading ? (
            <p>{t('loading')}</p>
          ) : (
            <div className='flex-grow overflow-y-auto border-2 border-neutral rounded p-2 min-h-0'>
              {cocktails
                ?.sort((a, b) => a.name.localeCompare(b.name))
                .map((cocktail) => (
                  <div key={cocktail.id} className='flex items-center my-1'>
                    <input
                      type='checkbox'
                      id={`cocktail-${cocktail.id}`}
                      checked={selectedCocktails.includes(cocktail.id)}
                      onChange={() => handleCocktailSelect(cocktail.id)}
                      className='mx-2'
                    />
                    <label htmlFor={`cocktail-${cocktail.id}`}>{cocktail.name}</label>
                  </div>
                ))}
            </div>
          )}
        </div>
        <div className='w-full sm:w-1/2 h-full flex flex-col sm:ml-4 mt-4 sm:mt-0'>
          <h2 className='font-bold mb-2 text-center text-xl text-secondary'>
            {t('recipeCalculation.neededIngredients')}
          </h2>
          <div className='flex-grow overflow-y-auto border-2 border-neutral rounded p-2 min-h-0'>
            {neededIngredients.map((ingredient) => (
              <Accordion
                key={ingredient.id}
                title={
                  <p>
                    {ingredient.name} ({t('recipeCalculation.inNRecipes', { n: ingredient.recipes.length })})
                  </p>
                }
              >
                <ul>
                  {ingredient.recipes
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((recipe) => (
                      <li key={recipe.id} className='flex items-center'>
                        <button type='button' className='text-danger' onClick={() => handleRemoveCocktail(recipe.id)}>
                          <RxCrossCircled size={20} />
                        </button>
                        <span className='ml-4'>{recipe.name}</span>
                      </li>
                    ))}
                </ul>
              </Accordion>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeCalculator;
