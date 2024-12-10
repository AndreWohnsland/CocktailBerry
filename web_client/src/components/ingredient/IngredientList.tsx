// components/IngredientList.tsx
import React, { useState } from 'react';
import Modal from 'react-modal';
import { FaPlus, FaTrashAlt, FaPen } from 'react-icons/fa';
import { IoHandLeft } from 'react-icons/io5';
import { deleteIngredient, postIngredient, updateIngredient, useIngredients } from '../../api/ingredients';
import { Ingredient, IngredientInput } from '../../types/models';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { confirmAndExecute, executeAndShow } from '../../utils';

const IngredientList: React.FC = () => {
  const { data: ingredients, isLoading, error, refetch } = useIngredients();
  const [selectedIngredient, setSelectedIngredient] = useState<IngredientInput | null>(null);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading ingredients</div>;

  const sortedIngredients = ingredients?.sort((a, b) => a.name.localeCompare(b.name));

  const handleIngredientClick = (ingredient: Ingredient) => {
    setSelectedIngredient({ ...ingredient });
  };

  const handleNewIngredientClick = () => {
    setSelectedIngredient({
      id: undefined,
      name: '',
      alcohol: 0,
      bottle_volume: 0,
      fill_level: 0,
      cost: 0,
      pump_speed: 0,
      hand: false,
      unit: '',
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    let newValue: string | number | boolean = value;
    if (type === 'checkbox') {
      newValue = checked;
    } else if (type === 'number') {
      const parsedValue = parseInt(value, 10);
      if (isNaN(parsedValue)) {
        return; // Abort if the value is not a valid number
      }
      newValue = parsedValue;
    }

    setSelectedIngredient((prev) => prev && { ...prev, [name]: newValue });
  };

  const closeModal = () => {
    setSelectedIngredient(null);
  };

  const handleDelete = async () => {
    const ingredientId = selectedIngredient?.id;
    if (!ingredientId) return;
    const success = await executeAndShow(() => deleteIngredient(ingredientId));
    if (success) {
      closeModal();
      refetch();
    }
  };

  const handlePost = async () => {
    const ingredient = selectedIngredient;
    if (!ingredient) return;
    const ingredientId = ingredient.id;
    const transaction = ingredientId ? updateIngredient : postIngredient;
    const success = await executeAndShow(() => transaction(ingredient));
    if (success) {
      closeModal();
      refetch();
    }
  };

  const isValidIngredient = (): boolean => {
    if (!selectedIngredient) return false;

    const { name, alcohol, bottle_volume, fill_level, cost, pump_speed } = selectedIngredient;

    if (!name.trim()) return false;
    if (!Number.isInteger(alcohol)) return false;
    if (!Number.isInteger(bottle_volume)) return false;
    if (!Number.isInteger(fill_level)) return false;
    if (!Number.isInteger(cost)) return false;
    if (!Number.isInteger(pump_speed)) return false;

    return true;
  };

  return (
    <div className='p-2 w-full max-w-3xl'>
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4'>
        <div className='col-span-2 md:col-span-3 w-full'>
          <button
            onClick={handleNewIngredientClick}
            className='flex justify-center items-center py-4 p-2 button-neutral-filled w-full'
          >
            <FaPlus size={25} />
            <span className='ml-4 text-xl'>New Ingredient</span>
          </button>
        </div>
        {sortedIngredients?.map((ingredient) => (
          <div key={ingredient.id}>
            <button
              onClick={() => handleIngredientClick(ingredient)}
              className='button-primary p-2 py-4 w-full flex justify-center items-center'
            >
              {ingredient.hand && <IoHandLeft size={20} className='mr-2' />}
              <span>{ingredient.name}</span>
            </button>
          </div>
        ))}
      </div>

      {selectedIngredient && (
        <Modal
          isOpen={!!selectedIngredient}
          onRequestClose={closeModal}
          className='modal'
          overlayClassName='overlay z-20'
        >
          <div className='px-4 rounded w-full h-full flex flex-col'>
            <div className='flex justify-between items-center mb-2'>
              <h2 className='text-xl font-bold text-secondary'>{selectedIngredient.name || 'New Ingredient'}</h2>
              <button onClick={closeModal} aria-label='close'>
                <AiOutlineCloseCircle className='text-danger' size={34} />
              </button>
            </div>
            <div className='flex-grow'></div>
            <form className='space-y-2 text-neutral grid-cols-2 grid h-xs:grid-cols-1'>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>Name:</p>
                <input
                  type='text'
                  name='name'
                  value={selectedIngredient.name}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>Alcohol:</p>
                <input
                  type='number'
                  name='alcohol'
                  value={selectedIngredient.alcohol}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center' style={{ whiteSpace: 'nowrap' }}>
                <p className='pr-2'>Bottle Volume:</p>
                <input
                  type='number'
                  name='bottle_volume'
                  value={selectedIngredient.bottle_volume}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>Cost:</p>
                <input
                  type='number'
                  name='cost'
                  value={selectedIngredient.cost}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <div className='flex justify-start items-center' style={{ whiteSpace: 'nowrap' }}>
                <p className='pr-2'>Pump Speed:</p>
                <input
                  type='number'
                  name='pump_speed'
                  value={selectedIngredient.pump_speed}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </div>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>Unit:</p>
                <input
                  type='text'
                  name='unit'
                  value={selectedIngredient.unit}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center col-span-2 h-xs:col-span-1'>
                <p className='text-primary pr-2'>Can only add by Hand:</p>
                <input
                  type='checkbox'
                  name='hand'
                  checked={selectedIngredient.hand}
                  onChange={handleChange}
                  className='checkbox-large'
                />
              </label>
            </form>
            <div className='flex-grow'></div>

            <div className='flex justify-between mt-2'>
              <button
                type='button'
                onClick={() => confirmAndExecute('Delete Ingredient', handleDelete)}
                className='button-danger-filled p-2 px-4 flex justify-between items-center'
              >
                <FaTrashAlt className='mr-2' />
                Delete
              </button>
              <button
                type='button'
                className={`p-2 px-4 flex justify-between items-center ${
                  isValidIngredient() ? 'button-primary-filled' : 'button-neutral-filled'
                }`}
                disabled={!isValidIngredient()}
                onClick={handlePost}
              >
                <FaPen className='mr-2' />
                {selectedIngredient?.id ? ' Apply' : ' Create'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default IngredientList;
