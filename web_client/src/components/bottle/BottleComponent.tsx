import React, { useState } from 'react';
import { Bottle, Ingredient } from '../../types/models';
import { updateBottle } from '../../api/bottles';
import { toast } from 'react-toastify';
import ProgressBar from '../common/ProgressBar';

interface BottleProps {
  bottle: Bottle;
  isToggled: boolean;
  onToggle: () => void;
  freeIngredients: Ingredient[];
  setFreeIngredients: (value: Ingredient[]) => void;
}

const BottleComponent: React.FC<BottleProps> = ({
  bottle,
  isToggled,
  onToggle,
  freeIngredients,
  setFreeIngredients,
}) => {
  const [selectedIngredientId, setSelectedIngredientId] = useState(bottle.ingredient?.id || 0);
  const [selectedIngredient, setSelectedIngredient] = useState<Ingredient | undefined>(bottle.ingredient);

  const getClass = () => {
    let color = 'border-primary text-primary';
    if (isToggled) {
      color = 'border-secondary bg-secondary text-background';
    }
    return `max-w-40 px-4 ml-2 border-2 font-bold rounded-md ${color}`;
  };

  const fillPercent = Math.max(
    Math.round(((selectedIngredient?.fill_level || 0) / (selectedIngredient?.bottle_volume || 1)) * 100),
    0,
  );

  const handleSelectionChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newIngredientId = parseInt(event.target.value, 10);
    let possibleIngredients = freeIngredients;
    let newIngredient = undefined;

    // Find the new ingredient only if the selected ID is not 0
    if (newIngredientId !== 0) {
      newIngredient = freeIngredients.find((ingredient) => ingredient.id === newIngredientId);
      if (newIngredient) {
        possibleIngredients = possibleIngredients.filter((ingredient) => ingredient.id !== newIngredientId);
      }
    }

    if (selectedIngredient) {
      possibleIngredients = [...freeIngredients, selectedIngredient];
    }

    try {
      await updateBottle(bottle.number, newIngredientId);
      setSelectedIngredient(newIngredient);
      setSelectedIngredientId(newIngredientId);
      setFreeIngredients(possibleIngredients);
    } catch (error) {
      console.error('Error updating bottle:', error);
      toast(`Error updating bottle: ${error}`, {
        toastId: 'bottle--update-error',
        pauseOnHover: false,
      });
    }
  };

  return (
    <>
      <div className='flex flex-row col-span-2 sm:col-span-1 mx-3 sm:mx-0'>
        <div className='place-content-center text-center text-secondary font-bold text-2xl mx-1 w-12'>
          {bottle.number}
        </div>
        <select
          className='select-base block w-full p-1.5'
          value={selectedIngredientId}
          onChange={handleSelectionChange}
        >
          {selectedIngredient && <option value={selectedIngredient.id}>{selectedIngredient.name}</option>}
          <option key={0} value={0}>
            -
          </option>
          {freeIngredients
            .sort((a, b) => a.name.localeCompare(b.name))
            .map((ingredient) => (
              <option key={ingredient.id} value={ingredient.id}>
                {ingredient.name}
              </option>
            ))}
        </select>
        <button onClick={onToggle} className={getClass()}>
          New
        </button>
      </div>
      <ProgressBar fillPercent={fillPercent} className='col-span-2 sm:col-span-1 mb-3 sm:mb-0 mx-3 sm:mx-0' />
    </>
  );
};

export default BottleComponent;
