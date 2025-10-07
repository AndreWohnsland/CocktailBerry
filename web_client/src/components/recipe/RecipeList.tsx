import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus } from 'react-icons/fa';
import { MdNoDrinks } from 'react-icons/md';
import { useNavigate } from 'react-router-dom';
import { enableAllRecipes, useCocktails } from '../../api/cocktails';
import { confirmAndExecute } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import TileButton from '../common/TileButton';

const RecipeList: React.FC = () => {
  const { data: cocktails, isLoading, error, refetch } = useCocktails(false, 10, false);
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();
  const navigate = useNavigate();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error?.message} />;

  let displayedCocktails = cocktails?.sort((a, b) => a.name.localeCompare(b.name));
  if (search) {
    displayedCocktails = displayedCocktails?.filter(
      (cocktail) =>
        cocktail.name.toLowerCase().includes(search.toLowerCase()) ??
        cocktail.ingredients.some((ingredient) => ingredient.name.toLowerCase().includes(search.toLowerCase())),
    );
  }

  const handleCocktailClick = (cocktailId: number) => {
    navigate(`/manage/recipes/${cocktailId}`);
  };

  const handleNewCocktailClick = () => {
    navigate('/manage/recipes/new');
  };

  const handleEnableAllRecipes = async () => {
    const success = await confirmAndExecute(t('recipes.enableAllRecipes'), enableAllRecipes);
    if (success) {
      refetch();
    }
  };

  return (
    <div className='p-2 pt-0 w-full max-w-3xl'>
      <SearchBar search={search} setSearch={setSearch}></SearchBar>
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4'>
        <div className='col-span-2 md:col-span-3 w-full flex flex-row gap-4'>
          <TileButton
            label={t('new')}
            style='secondary'
            filled
            textSize='lg'
            icon={FaPlus}
            iconSize={25}
            onClick={handleNewCocktailClick}
          />
          <TileButton
            label={t('recipes.enableAll')}
            style='neutral'
            filled
            textSize='lg'
            onClick={handleEnableAllRecipes}
          />
        </div>
        {displayedCocktails?.map((cocktail) => (
          <TileButton
            label={cocktail.name}
            icon={cocktail.virgin_available ? MdNoDrinks : undefined}
            onClick={() => handleCocktailClick(cocktail.id)}
            key={cocktail.id}
            passive={!cocktail.enabled}
          />
        ))}
      </div>
    </div>
  );
};

export default RecipeList;
