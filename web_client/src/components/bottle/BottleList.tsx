import React, { useEffect, useState } from 'react';
import { refillBottle, useBottles } from '../../api/bottles';
import { useIngredients } from '../../api/ingredients';
import BottleComponent from './BottleComponent';
import { FaGear } from 'react-icons/fa6';
import { Ingredient } from '../../types/models';
import { toast, ToastContainer } from 'react-toastify';

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

  useEffect(() => {
    if (bottles && ingredients) {
      const bottleIngredients = bottles.map((bottle) => bottle.ingredient?.id);
      const missingIngredients = ingredients.filter((ingredient) => !bottleIngredients.includes(ingredient.id));
      setFreeIngredients(missingIngredients);
    }
  }, [bottles, ingredients]);

  if (bottlesLoading || ingredientsLoading || isFetching) {
    return <div>Loading...</div>;
  }

  if (bottlesError || ingredientsError) {
    return <div>Error: {bottlesError?.message || ingredientsError?.message}</div>;
  }

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
    try {
      await refillBottle(toggledNumbers);
      await bottleRefetch();
    } catch (error) {
      console.error('Error refilling bottle:', error);
      toast(`Error refilling bottle: ${error}`, {
        toastId: 'bottle-refill-error',
        pauseOnHover: false,
      });
      return;
    }
    setToggledBottles({});
  };

  return (
    <>
      <ToastContainer position='top-center' />
      <div
        className='grid grid-cols-5 gap-2 pt-4 px-1 max-w-7xl w-full'
        style={{ gridTemplateColumns: '2fr 3fr 6fr 4fr 1fr' }}
      >
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
        <button className='sticky-button button-primary-filled col-span-2 p-2' onClick={handleApply}>
          Apply
        </button>
        <button className='sticky-button button-primary p-2'>Change</button>
        <button className='sticky-button button-primary-filled p-2'>Available</button>
        <button className='sticky-button button-primary-filled flex justify-center items-center max-w-12'>
          <FaGear size={30} />
        </button>
      </div>
    </>
  );
};

export default BottleList;
