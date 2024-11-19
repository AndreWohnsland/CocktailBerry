import React, { useState } from 'react';
import { Bottle, Ingredient } from '../../types/models';
import { updateBottle } from '../../api/bottles';
import { toast } from 'react-toastify';

interface BottleProps {
  bottle: Bottle;
  freeIngredients: Ingredient[];
  setFreeIngredients: (value: Ingredient[]) => void;
}

const BottleComponent: React.FC<BottleProps> = ({ bottle, freeIngredients, setFreeIngredients }) => {
  const [isNew, setIsNew] = useState(false);
  const [selectedIngredientId, setSelectedIngredientId] = useState(bottle.ingredient?.id);
  const [selectedIngredient, setSelectedIngredient] = useState<Ingredient | undefined>(bottle.ingredient);

  const getClass = () => {
    const color = isNew ? 'secondary' : 'primary';
    return `max-w-20 border-2 font-bold rounded-md border-${color} text-${color}`;
  };

  const fillPercent = Math.round(
    ((bottle.ingredient?.fill_level || 0) / (bottle.ingredient?.bottle_volume || 1)) * 100,
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
      <button onClick={() => setIsNew(!isNew)} className={getClass()}>
        New
      </button>
      <div className='flex items-center justify-end'>
        <span className='text-right text-secondary pr-1'>{bottle.ingredient?.name || 'No Name'}:</span>
      </div>
      <div
        className='border-2 border-neutral bg-neutral text-background font-bold rounded-full text-center overflow-hidden flex items-center justify-center'
        style={{ position: 'relative' }}
      >
        <div
          className='bg-primary rounded-full'
          style={{ width: `${fillPercent}%`, height: '100%', position: 'absolute', left: 0, top: 0 }}
        ></div>
        <span style={{ position: 'relative', zIndex: 1 }}>{fillPercent}%</span>
      </div>
      <select
        className='bg-background border border-neutral text-primary text-sm rounded-lg focus:border-primary block w-full p-2'
        value={selectedIngredientId}
        onChange={handleSelectionChange}
      >
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
