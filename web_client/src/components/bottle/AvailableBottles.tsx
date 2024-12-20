import React, { useEffect, useState } from 'react';
import { postAvailableIngredients, useAvailableIngredients, useIngredients } from '../../api/ingredients';
import { Ingredient } from '../../types/models';
import ListView from './ListView';
import { useNavigate } from 'react-router-dom';
import { FaPlusCircle, FaMinusCircle } from 'react-icons/fa';
import { toast } from 'react-toastify';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';

const AvailableBottles: React.FC = () => {
  const { data: ingredients, error: ingredientsError, isLoading: ingredientsLoading } = useIngredients();
  const { data: available, error: availableError, isLoading: availableLoading } = useAvailableIngredients();
  const [freeIngredients, setFreeIngredients] = useState<Ingredient[]>([]);
  const [availableIngredients, setAvailableIngredients] = useState<Ingredient[]>([]);
  const [selectedAvailable, setSelectedAvailable] = useState<Ingredient[]>([]);
  const [selectedFree, setSelectedFree] = useState<Ingredient[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    setFreeIngredients((ingredients ?? []).filter((ingredient) => !(available ?? []).includes(ingredient.id)));
    setAvailableIngredients((ingredients ?? []).filter((ingredient) => (available ?? []).includes(ingredient.id)));
  }, [ingredients, available]);

  if (ingredientsLoading || availableLoading) return <LoadingData />;
  if (ingredientsError || availableError)
    return <ErrorComponent text={ingredientsError?.message || availableError?.message} />;

  const moveSelected = (
    setFrom: React.Dispatch<React.SetStateAction<Ingredient[]>>,
    setTo: React.Dispatch<React.SetStateAction<Ingredient[]>>,
    selected: Ingredient[],
    setSelected: React.Dispatch<React.SetStateAction<Ingredient[]>>,
  ) => {
    setTo((prev) => [...prev, ...selected]);
    setFrom((prev) => prev.filter((ingredient) => !selected.includes(ingredient)));
    setSelected([]);
  };

  const updateAvailable = async () => {
    try {
      await postAvailableIngredients(availableIngredients.map((ingredient) => ingredient.id));
      navigate(-1);
    } catch (error) {
      console.error('Error updating available ingredients:', error);
      toast(`Error setting ingredients: ${error}`, {
        toastId: 'bottle-available-error',
        pauseOnHover: false,
      });
    }
  };

  return (
    <div className='max-w-7xl w-full px-1'>
      <div className='flex flex-col sm:flex-row justify-start items-start w-full h-full sm:h-[70vh]'>
        <div className='w-full sm:w-1/2 h-[50vh] sm:h-full'>
          <h2 className='font-bold mb-2 text-center text-xl text-secondary'>Available</h2>
          <ListView
            ingredientList={availableIngredients}
            setSelected={setSelectedAvailable}
            selected={selectedAvailable}
          />
        </div>
        <div className='flex flex-row sm:flex-col justify-center items-center mx-0 sm:mx-2 mt-9 w-full h-full sm:w-16'>
          <button
            className='button-primary-filled p-2 my-2 mr-2 sm:mb-2 sm:mx-2 sm:my-0 h-1/2 w-1/2 sm:w-full items-center justify-center flex'
            onClick={() => moveSelected(setFreeIngredients, setAvailableIngredients, selectedFree, setSelectedFree)}
          >
            <FaPlusCircle size={40} />
          </button>
          <button
            className='button-primary p-2 my-2 sm:mx-2 sm:my-0 h-1/2 w-1/2 sm:w-full items-center justify-center flex'
            onClick={() =>
              moveSelected(setAvailableIngredients, setFreeIngredients, selectedAvailable, setSelectedAvailable)
            }
          >
            <FaMinusCircle size={40} />
          </button>
        </div>
        <div className='w-full sm:w-1/2 h-[50vh] sm:h-full'>
          <h2 className='font-bold mb-2 text-center text-xl text-secondary'>Possible to Add</h2>

          <ListView ingredientList={freeIngredients} setSelected={setSelectedFree} selected={selectedFree} />
        </div>
      </div>
      <div className='w-full flex justify-between mt-12'>
        <button onClick={() => navigate(-1)} className='button-primary p-2 w-1/2 mr-2'>
          Back
        </button>
        <button onClick={updateAvailable} className='button-primary-filled p-2 w-1/2'>
          Apply
        </button>
      </div>
    </div>
  );
};

export default AvailableBottles;
