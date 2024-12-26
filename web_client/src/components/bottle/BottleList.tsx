import React, { useEffect, useState } from 'react';
import { refillBottle, useBottles } from '../../api/bottles';
import { useIngredients } from '../../api/ingredients';
import BottleComponent from './BottleComponent';
import { Ingredient } from '../../types/models';
import { useNavigate } from 'react-router-dom';
import { executeAndShow } from '../../utils';
import LoadingData from '../common/LoadingData';
import ErrorComponent from '../common/ErrorComponent';
import { useTranslation } from 'react-i18next';

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
    return <ErrorComponent text={bottlesError?.message || ingredientsError?.message} />;

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
    <>
      <div className='px-1 max-w-7xl w-full h-full'>
        <div className='grid grid-cols-2 place-items-stretch gap-2 w-full h-full'>
          {bottles?.map((bottle) => (
            <BottleComponent
              key={bottle.number}
              bottle={bottle}
              isToggled={toggledBottles[bottle.number] || false}
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
      </div>
    </>
  );
};

export default BottleList;
