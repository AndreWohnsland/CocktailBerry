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
  const [selectedIngredientId, setSelectedIngredientId] = useState(bottle.ingredient?.id);
  const [selectedIngredient, setSelectedIngredient] = useState<Ingredient | undefined>(bottle.ingredient);

  const getClass = () => {
    let color = 'border-primary text-primary';
    if (isToggled) {
      color = 'border-secondary bg-secondary text-background';
    }
    return `max-w-20 border-2 font-bold rounded-md ${color}`;
  };

  const fillPercent = Math.max(
    Math.round(((selectedIngredient?.fill_level || 0) / (selectedIngredient?.bottle_volume || 1)) * 100),
    0,
  );

  const handleSelectionChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newIngredientId = parseInt(event.target.value, 10);
    try {
      await updateBottle(bottle.number, newIngredientId);
    } catch (error) {
      console.error('Error updating bottle:', error);
      toast(`Error updating bottle: ${error}`, {
        toastId: 'bottle--update-error',
        pauseOnHover: false,
      });
      return;
    }
    let possibleIngredients = freeIngredients;
    if (selectedIngredient !== undefined) {
      possibleIngredients = [...freeIngredients, selectedIngredient];
    }
    const newIngredient = freeIngredients.find((ingredient) => ingredient.id === newIngredientId);
    setSelectedIngredient(newIngredient);
    if (newIngredient) {
      possibleIngredients = possibleIngredients.filter((ingredient) => ingredient.id !== newIngredientId);
    }
    setFreeIngredients(possibleIngredients);
    setSelectedIngredientId(newIngredientId);
  };

  return (
    <>
      <button onClick={onToggle} className={getClass()}>
        New
      </button>
      <div className='flex items-center justify-end'>
        <span className='text-right text-secondary pr-1'>{selectedIngredient?.name || 'No Name'}:</span>
      </div>
      <ProgressBar fillPercent={fillPercent} />
      <select className='select-base block w-full p-1.5' value={selectedIngredientId} onChange={handleSelectionChange}>
        {selectedIngredient && <option value={selectedIngredient.id}>{selectedIngredient.name}</option>}
        {freeIngredients.map((ingredient) => (
          <option key={ingredient.id} value={ingredient.id}>
            {ingredient.name}
          </option>
        ))}
      </select>
      <div className='place-content-center text-center text-secondary font-bold max-w-12 text-2xl'>{bottle.number}</div>
    </>
  );
};

export default BottleComponent;
