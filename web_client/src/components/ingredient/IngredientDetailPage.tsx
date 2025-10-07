import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPen, FaPlus, FaTrashAlt } from 'react-icons/fa';
import { useNavigate, useParams } from 'react-router-dom';
import { deleteIngredient, postIngredient, updateIngredient, useIngredient, useIngredients } from '../../api/ingredients';
import { IngredientInput } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import CloseButton from '../common/CloseButton';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';

const IngredientDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const isNew = id === 'new';
  const ingredientId = isNew ? undefined : id ? parseInt(id, 10) : undefined;
  const { data: ingredient, error, isLoading } = useIngredient(ingredientId);
  const { refetch } = useIngredients();
  const [selectedIngredient, setSelectedIngredient] = useState<IngredientInput | null>(null);

  useEffect(() => {
    if (isNew) {
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
    } else if (ingredient) {
      setSelectedIngredient({ ...ingredient });
    }
  }, [ingredient, isNew]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    let newValue: string | number | boolean = value;
    if (type === 'checkbox') {
      newValue = checked;
    } else if (type === 'number') {
      const parsedValue = parseInt(value, 10);
      if (isNaN(parsedValue)) {
        return;
      }
      newValue = parsedValue;
    }

    setSelectedIngredient((prev) => prev && { ...prev, [name]: newValue });
  };

  const handleClose = () => {
    navigate('/manage/ingredients');
  };

  const handleDelete = async () => {
    const id = selectedIngredient?.id;
    if (!id) return;
    const success = await confirmAndExecute(t('ingredients.deleteIngredient'), () => deleteIngredient(id));
    if (success) {
      handleClose();
      refetch();
    }
  };

  const handlePost = async () => {
    const ingredient = selectedIngredient;
    if (!ingredient) return;
    const id = ingredient.id;
    const transaction = id ? updateIngredient : postIngredient;
    const success = await executeAndShow(() => transaction(ingredient));
    if (success) {
      handleClose();
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

  if (isLoading && !isNew) return <LoadingData />;
  if (error && !isNew) return <ErrorComponent text={error.message} />;
  if (!selectedIngredient) return <ErrorComponent text='Ingredient not found' />;

  return (
    <div className='p-2 pt-4 w-full max-w-3xl'>
      <div className='bg-background border-2 border-primary rounded-lg p-4 w-full'>
        <div className='px-1 rounded w-full flex flex-col'>
          <div className='flex justify-between items-center mb-2'>
            <p className='text-xl font-bold text-secondary'>
              {selectedIngredient.name || t('ingredients.newIngredient')}
            </p>
            <CloseButton onClick={handleClose} />
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
      </div>
    </div>
  );
};

export default IngredientDetailPage;
