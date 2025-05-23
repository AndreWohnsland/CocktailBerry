import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { refillBottle, useBottles } from '../../api/bottles';
import { useIngredients } from '../../api/ingredients';
import { Ingredient } from '../../types/models';
import { executeAndShow } from '../../utils';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import BottleComponent from './BottleComponent';

const BottleList: React.FC = () => {
  const {
    data: bottles,
    error: bottlesError,
    isLoading: bottlesLoading,
    isFetching,
    refetch: bottleRefetch,
  } = useBottles();
  const { data: ingredients, error: ingredientsError, isLoading: ingredientsLoading } = useIngredients(false);
  const [freeIngredients, setFreeIngredients] = useState<Ingredient[]>([]);
  const [toggledBottles, setToggledBottles] = useState<{ [key: number]: boolean }>({});
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    if (bottles && ingredients) {
      const bottleIngredients = bottles.map((bottle) => bottle.ingredient?.id);
      const missingIngredients = ingredients.filter((ingredient) => !bottleIngredients.includes(ingredient.id));
      setFreeIngredients(missingIngredients);
    }
  }, [bottles, ingredients]);

  if (bottlesLoading || ingredientsLoading || isFetching) return <LoadingData />;
  if (bottlesError || ingredientsError)
    return <ErrorComponent text={bottlesError?.message ?? ingredientsError?.message} />;

  const handleToggle = (bottleNumber: number) => {
    setToggledBottles((prev) => ({
      ...prev,
      [bottleNumber]: !prev[bottleNumber],
    }));
  };

  const handleApply = async () => {
    const toggledNumbers = Object.keys(toggledBottles)
      .filter((key) => toggledBottles[Number(key)])
      .map(Number);
    if (!toggledNumbers.length) return;
    const success = await executeAndShow(() => refillBottle(toggledNumbers));
    if (success) {
      await bottleRefetch();
      setToggledBottles({});
    }
  };

  return (
    <div className='max-w-7xl w-full h-full flex flex-col px-2'>
      <div className='grow'></div>
      <div className='w-full grow gap-2 flex flex-col overflow-y-auto'>
        {bottles?.map((bottle) => (
          <BottleComponent
            key={bottle.number}
            bottle={bottle}
            isToggled={toggledBottles[bottle.number] ?? false}
            onToggle={() => handleToggle(bottle.number)}
            freeIngredients={freeIngredients}
            setFreeIngredients={setFreeIngredients}
          />
        ))}
      </div>
      <div className='sticky-bottom w-full grid grid-cols-2 gap-2 py-1 mt-2 bg-background'>
        <button className='button-primary-filled p-2' onClick={handleApply}>
          {t('bottles.applyNew')}
        </button>
        <button className='button-primary p-2 ' onClick={() => navigate('/manage/bottles/available')}>
          {t('bottles.available')}
        </button>
      </div>
      <div className='grow'></div>
    </div>
  );
};

export default BottleList;
