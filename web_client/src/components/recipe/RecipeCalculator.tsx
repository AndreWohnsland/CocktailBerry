import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCalculator } from 'react-icons/fa6';
import { calculateOptimal, useCocktails } from '../../api/cocktails.ts';
import type { CocktailIngredient } from '../../types/models.ts';
import { confirmAndExecute } from '../../utils.tsx';
import Accordion from '../common/Accordion';
import Button from '../common/Button/index.tsx';
import CloseButton from '../common/CloseButton/index.tsx';
import TextHeader from '../common/TextHeader/index.tsx';

type CocktailIngredientWithRecipes = CocktailIngredient & { recipes: { id: number; name: string }[] };

function RecipeCalculator() {
  const { t } = useTranslation();
  const [selectedCocktails, setSelectedCocktails] = useState<number[]>([]);
  const [nIngredients, setNIngredients] = useState<number>(10);
  const { data: cocktails } = useCocktails(false, 0, false);

  // Select-all checkbox state
  const allCount = cocktails?.length ?? 0;
  const allSelected = allCount > 0 && selectedCocktails.length === allCount;

  const handleToggleAll = (checked: boolean) => {
    if (!cocktails) return;
    setSelectedCocktails(checked ? cocktails.map((c) => c.id) : []);
  };

  const handleCocktailSelect = (id: number) => {
    setSelectedCocktails((prev) =>
      prev.includes(id) ? prev.filter((cocktailId) => cocktailId !== id) : [...prev, id],
    );
  };

  const handleRemoveCocktail = (id: number) => {
    setSelectedCocktails((prev) => prev.filter((cocktailId) => cocktailId !== id));
  };

  const handleCalculate = async () => {
    await confirmAndExecute(t('recipeCalculation.confirmCalculation'), async () => {
      const result = await calculateOptimal(nIngredients, 'ilp');
      setSelectedCocktails(result.cocktails.map((c) => c.id));
    });
  };

  const ingredientWithRecipes = useMemo(() => {
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
    return [...ingredients.values()].sort((a, b) => {
      const diff = b.recipes.length - a.recipes.length;
      return diff !== 0 ? diff : a.name.localeCompare(b.name);
    });
  }, [cocktails, selectedCocktails]);

  return (
    <div className='max-w-7xl w-full px-1 flex flex-col h-full'>
      <TextHeader text={t('recipeCalculation.title')} space={4} />
      <div className='w-full flex items-center justify-center gap-3 px-2 mb-3'>
        <label htmlFor='num-ingredients' className='font-medium text-center'>
          {t('recipeCalculation.numberIngredients')}
        </label>
        <input
          id='num-ingredients'
          type='number'
          min={1}
          value={nIngredients}
          onChange={(e) => setNIngredients(Math.max(1, Number(e.currentTarget.value)))}
          className='input-base-large max-w-20'
        />
        <Button label={t('recipeCalculation.optimize')} filled onClick={handleCalculate} icon={FaCalculator} />
      </div>
      <div className='flex-grow flex flex-col sm:flex-row justify-start items-start w-full h-full sm:h-[70vh] h-md:mb-6 mb-2'>
        <div className='w-full sm:w-1/2 h-full flex flex-col'>
          <TextHeader
            text={t('recipeCalculation.cocktailsHeader', {
              count: selectedCocktails.length,
            })}
            space={2}
            subheader
          />

          <div className='flex items-center mb-2'>
            <input
              type='checkbox'
              id='cocktail-select-all'
              checked={allSelected}
              onChange={(e) => handleToggleAll(e.currentTarget.checked)}
              disabled={!cocktails || cocktails.length === 0}
              className='checkbox-large mr-2 ml-4'
            />
            <label htmlFor='cocktail-select-all'>{t('recipeCalculation.selectAll')}</label>
          </div>
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
                    className='checkbox-large mx-2'
                  />
                  <label htmlFor={`cocktail-${cocktail.id}`}>{cocktail.name}</label>
                </div>
              ))}
          </div>
        </div>
        <div className='w-full sm:w-1/2 h-full flex flex-col sm:ml-4 mt-4 sm:mt-0'>
          <TextHeader
            text={t('recipeCalculation.neededIngredientsHeader', {
              count: ingredientWithRecipes.length,
            })}
            subheader
            space={2}
          />
          <div className='flex-grow overflow-y-auto border-2 border-neutral rounded p-2 min-h-0'>
            {ingredientWithRecipes.map((ingredient) => (
              <Accordion
                key={ingredient.id}
                title={
                  <p>
                    <span className='font-bold'>{ingredient.name}</span> (
                    {t('recipeCalculation.inNRecipes', { n: ingredient.recipes.length })})
                  </p>
                }
              >
                <ul>
                  {ingredient.recipes
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map((recipe) => (
                      <li key={recipe.id} className='flex items-center'>
                        <CloseButton iconSize={25} onClick={() => handleRemoveCocktail(recipe.id)} />
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
