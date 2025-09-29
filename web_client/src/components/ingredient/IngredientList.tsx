// components/IngredientList.tsx
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPen, FaPlus, FaTrashAlt } from 'react-icons/fa';
import { IoHandLeft } from 'react-icons/io5';
import Modal from 'react-modal';
import { deleteIngredient, postIngredient, updateIngredient, useIngredients } from '../../api/ingredients';
import { Ingredient, IngredientInput } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import CloseButton from '../common/CloseButton';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import TileButton from '../common/TileButton';

const IngredientList: React.FC = () => {
  const { data: ingredients, isLoading, error, refetch } = useIngredients();
  const [selectedIngredient, setSelectedIngredient] = useState<IngredientInput | null>(null);
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  let displayedIngredients = ingredients?.sort((a, b) => a.name.localeCompare(b.name));
  if (search) {
    displayedIngredients = displayedIngredients?.filter((ingredient) =>
      ingredient.name.toLowerCase().includes(search.toLowerCase()),
    );
  }

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
      pump_speed: 100,
      hand: false,
      unit: 'ml',
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
    const success = await confirmAndExecute(t('ingredients.deleteIngredient'), () => deleteIngredient(ingredientId));
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
            onClick={() => handleIngredientClick(ingredient)}
            key={ingredient.id}
          />
        ))}
      </div>

      <Modal
        isOpen={!!selectedIngredient}
        onRequestClose={closeModal}
        className='modal'
        overlayClassName='overlay z-20'
      >
        {selectedIngredient && (
          <div className='px-1 rounded w-full h-full flex flex-col'>
            <div className='flex justify-between items-center mb-2'>
              <p className='text-xl font-bold text-secondary'>
                {selectedIngredient.name ?? t('ingredients.newIngredient')}
              </p>
              <CloseButton onClick={closeModal} />
            </div>
            <div className='flex-grow'></div>
            <form className='space-y-2 text-neutral grid-cols-2 grid h-xs:grid-cols-1'>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('ingredients.name')}:</p>
                <input
                  type='text'
                  name='name'
                  value={selectedIngredient.name}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('ingredients.alcohol')}:</p>
                <input
                  type='number'
                  name='alcohol'
                  value={selectedIngredient.alcohol}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center' style={{ whiteSpace: 'nowrap' }}>
                <p className='pr-2'>{t('ingredients.bottleVolume')}:</p>
                <input
                  type='number'
                  name='bottle_volume'
                  value={selectedIngredient.bottle_volume}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('ingredients.cost')}:</p>
                <input
                  type='number'
                  name='cost'
                  value={selectedIngredient.cost}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <div className='flex justify-start items-center' style={{ whiteSpace: 'nowrap' }}>
                <p className='pr-2'>{t('ingredients.pumpSpeed')}:</p>
                <input
                  type='number'
                  name='pump_speed'
                  value={selectedIngredient.pump_speed}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </div>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('ingredients.unit')}:</p>
                <input
                  type='text'
                  name='unit'
                  value={selectedIngredient.unit}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <label className='flex justify-center items-center col-span-2 h-xs:col-span-1'>
                <p className='text-primary pr-2'>{t('ingredients.onlyAddByHand')}:</p>
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
                onClick={handleDelete}
                disabled={!selectedIngredient?.id}
                className={`${
                  !selectedIngredient?.id && 'disabled'
                } button-danger-filled p-2 px-4 flex justify-between items-center`}
              >
                <FaTrashAlt className='mr-2' />
                {t('delete')}
              </button>
              <button
                type='button'
                className={`p-2 px-4 flex justify-between items-center button-primary-filled ${
                  !isValidIngredient() && 'disabled'
                }`}
                disabled={!isValidIngredient()}
                onClick={handlePost}
              >
                {selectedIngredient?.id ? <FaPen className='mr-2' /> : <FaPlus className='mr-2' />}
                {selectedIngredient?.id ? t('apply') : t('create')}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IngredientList;
