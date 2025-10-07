// components/IngredientList.tsx
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus } from 'react-icons/fa';
import { IoHandLeft } from 'react-icons/io5';
import { useNavigate } from 'react-router-dom';
import { useIngredients } from '../../api/ingredients';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import TileButton from '../common/TileButton';

const IngredientList: React.FC = () => {
  const { data: ingredients, isLoading, error } = useIngredients();
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();
  const navigate = useNavigate();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  let displayedIngredients = ingredients?.sort((a, b) => a.name.localeCompare(b.name));
  if (search) {
    displayedIngredients = displayedIngredients?.filter((ingredient) =>
      ingredient.name.toLowerCase().includes(search.toLowerCase()),
    );
  }

  const handleIngredientClick = (ingredientId: number) => {
    navigate(`/manage/ingredients/${ingredientId}`);
  };

  const handleNewIngredientClick = () => {
    navigate('/manage/ingredients/new');
  };

  return (
    <div className='p-2 pt-0 w-full max-w-3xl'>
      <SearchBar search={search} setSearch={setSearch}></SearchBar>
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4'>
        <div className='col-span-2 md:col-span-3 w-full'>
          <TileButton
            label={t('new')}
            textSize='lg'
            style='secondary'
            filled
            icon={FaPlus}
            iconSize={25}
            onClick={handleNewIngredientClick}
          />
        </div>
        {displayedIngredients?.map((ingredient) => (
          <TileButton
            label={ingredient.name}
            icon={ingredient.hand ? IoHandLeft : undefined}
            onClick={() => handleIngredientClick(ingredient.id)}
            key={ingredient.id}
          />
        ))}
      </div>
    </div>
  );
};

export default IngredientList;
