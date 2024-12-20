import React, { useRef, useState } from 'react';
import Modal from 'react-modal';
import { FaPlus, FaTrashAlt, FaPen, FaUpload } from 'react-icons/fa';
import { AiOutlineCloseCircle } from 'react-icons/ai';
import { MdNoDrinks } from 'react-icons/md';
import {
  deleteCocktail,
  deleteCocktailImage,
  enableAllRecipes,
  postCocktail,
  updateCocktail,
  uploadCocktailImage,
  useCocktails,
} from '../../api/cocktails';
import { Cocktail, CocktailInput } from '../../types/models';
import { useIngredients } from '../../api/ingredients';
import { confirmAndExecute, errorToast, executeAndShow } from '../../utils';
import LoadingData from '../common/LoadingData';
import ErrorComponent from '../common/ErrorComponent';

const RecipeList: React.FC = () => {
  const { data: cocktails, isLoading, error, refetch } = useCocktails(false, 10, false);
  const [selectedCocktail, setSelectedCocktail] = useState<CocktailInput | null>(null);
  const { data: ingredients, isLoading: ingredientsLoading, error: ingredientsError } = useIngredients();
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (isLoading || ingredientsLoading) return <LoadingData />;
  if (error || ingredientsError) return <ErrorComponent text={error?.message || ingredientsError?.message} />;

  const sortedCocktails = cocktails?.sort((a, b) => a.name.localeCompare(b.name));

  const handleCocktailClick = (cocktail: Cocktail) => {
    setSelectedCocktail({
      id: cocktail.id,
      name: cocktail.name,
      enabled: cocktail.enabled,
      virgin_available: cocktail.virgin_available,
      image: cocktail.image,
      default_image: cocktail.default_image,
      ingredients: cocktail.ingredients.map((ingredient) => ({
        id: ingredient.id,
        amount: ingredient.amount,
        recipe_order: ingredient.recipe_order,
      })),
    });
  };

  const handleNewCocktailClick = () => {
    setSelectedCocktail({
      id: undefined,
      name: '',
      enabled: true,
      virgin_available: false,
      image: '',
      default_image: '',
      ingredients: [],
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSelectedCocktail((prev) => prev && { ...prev, [name]: type === 'checkbox' ? checked : value });
  };

  const handleIngredientChange = (index: number, e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSelectedCocktail((prev) => {
      if (!prev) return null;
      const ingredients = [...prev.ingredients];
      if (e.target.tagName === 'SELECT') {
        ingredients[index] = { ...ingredients[index], id: Number(value) };
      } else {
        ingredients[index] = { ...ingredients[index], [name]: Number(value) };
      }
      return { ...prev, ingredients };
    });
  };

  const handleEnableAllRecipes = async () => {
    const success = await confirmAndExecute('Enable all Recipes', enableAllRecipes);
    if (success) {
      refetch();
    }
  };

  const handleUploadImage = async () => {
    if (!selectedCocktail?.id) return;
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      errorToast('Please select a file before uploading.', 'No File');
      return;
    }
    const success = await executeAndShow(() => uploadCocktailImage(selectedCocktail.id!, file));
    if (success) {
      refetch();
    }
  };

  const handleDeleteImage = async () => {
    if (!selectedCocktail?.id) return;
    const success = await confirmAndExecute('Delete existing user image', () =>
      deleteCocktailImage(selectedCocktail.id!),
    );
    if (success) {
      refetch();
    }
  };

  const addIngredient = () => {
    setSelectedCocktail((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        ingredients: [...prev.ingredients, { id: 0, amount: 1, recipe_order: 1 }],
      };
    });
  };

  const removeIngredient = (index: number) => {
    setSelectedCocktail((prev) => {
      if (!prev) return null;
      const ingredients = prev.ingredients.filter((_, i) => i !== index);
      return { ...prev, ingredients };
    });
  };

  const closeModal = () => {
    setSelectedCocktail(null);
  };

  const isValidCocktail = (): boolean => {
    if (!selectedCocktail) return false;
    const { name, ingredients } = selectedCocktail;
    if (!name.trim()) return false;
    if (ingredients.length <= 1) return false;
    if (ingredients.some((ingredient) => !ingredient.id || !ingredient.amount || !ingredient.recipe_order))
      return false;
    return true;
  };

  const handleDelete = async () => {
    const cocktailId = selectedCocktail?.id;
    if (!cocktailId) return;
    const success = await executeAndShow(() => deleteCocktail(cocktailId));
    if (success) {
      closeModal();
      refetch();
    }
  };

  const handlePost = async () => {
    const cocktail = selectedCocktail;
    if (!cocktail) return;
    const cocktailId = cocktail.id;
    const transaction = cocktailId ? updateCocktail : postCocktail;
    const success = await executeAndShow(() => transaction(cocktail));
    if (success) {
      closeModal();
      refetch();
    }
  };

  return (
    <div className='p-2 w-full max-w-3xl'>
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4'>
        <div className='col-span-2 md:col-span-3 w-full flex flex-row gap-4'>
          <button
            onClick={handleNewCocktailClick}
            className='flex justify-center items-center py-3 p-2 button-secondary-filled w-full'
          >
            <FaPlus size={25} />
            <span className='ml-4 text-xl'>New</span>
          </button>
          <button
            onClick={handleEnableAllRecipes}
            className='flex justify-center items-center py-3 p-2 button-neutral-filled w-full'
          >
            <span className='ml-4 text-xl'>Enable All</span>
          </button>
        </div>
        {sortedCocktails?.map((cocktail) => (
          <button
            key={cocktail.id}
            onClick={() => handleCocktailClick(cocktail)}
            className={`p-2 py-4 w-full flex justify-center items-center ${
              cocktail.enabled ? 'button-primary' : 'button-neutral'
            }`}
          >
            {cocktail.virgin_available && <MdNoDrinks size={20} className='mr-2' />}
            <span>{cocktail.name}</span>
          </button>
        ))}
      </div>

      {selectedCocktail && (
        <Modal
          isOpen={!!selectedCocktail}
          onRequestClose={closeModal}
          className='modal'
          overlayClassName='overlay z-20'
        >
          <div className='px-1 rounded w-full h-full flex flex-col'>
            <div className='flex justify-between items-center mb-2'>
              <h2 className='text-xl font-bold text-secondary'>{selectedCocktail.name || 'New Recipe'}</h2>
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
                  value={selectedCocktail.name}
                  onChange={handleChange}
                  className='input-base w-full p-2 mr-2'
                />
              </label>
              <div className='flex flex-row items-center w-full justify-center'>
                <label className='flex justify-center items-center pr-4'>
                  <p className='pr-2'>Enabled:</p>
                  <input
                    type='checkbox'
                    name='enabled'
                    checked={selectedCocktail.enabled}
                    onChange={handleChange}
                    className='checkbox-large'
                  />
                </label>
                <label className='flex justify-center items-center'>
                  <p className='pr-2'>Virgin Available:</p>
                  <input
                    type='checkbox'
                    name='virgin_available'
                    checked={selectedCocktail.virgin_available}
                    onChange={handleChange}
                    className='checkbox-large'
                  />
                </label>
              </div>
              {selectedCocktail.ingredients.map((ingredient, index) => (
                <div key={index} className='flex items-center'>
                  <select
                    value={ingredient.id}
                    onChange={(e) => handleIngredientChange(index, e)}
                    className='select-base p-2 mr-2'
                  >
                    <option value=''>Select Ingredient</option>
                    {ingredients?.map((ing) => (
                      <option key={ing.id} value={ing.id}>
                        {ing.name}
                      </option>
                    ))}
                  </select>
                  <label className='flex justify-center items-center'>
                    <input
                      type='number'
                      name='amount'
                      value={ingredient.amount}
                      onChange={(e) => handleIngredientChange(index, e)}
                      className='input-base p-2'
                    />
                    <p className='px-1'>ml</p>
                  </label>
                  <input
                    type='number'
                    name='recipe_order'
                    value={ingredient.recipe_order}
                    onChange={(e) => handleIngredientChange(index, e)}
                    className='input-base p-2 mr-1 max-w-8'
                  />
                  <button type='button' onClick={() => removeIngredient(index)} className='button-danger p-2 mr-1'>
                    <FaTrashAlt />
                  </button>
                </div>
              ))}
              <button
                type='button'
                onClick={addIngredient}
                className='button-neutral p-1 flex items-center justify-center'
              >
                <FaPlus className='mr-2' />
                Add Ingredient
              </button>
              <div className='flex items-center pt-1'>
                <button type='button' onClick={handleUploadImage} className='button-secondary p-2 mr-1'>
                  <FaUpload />
                </button>
                <input type='file' accept='image/*' ref={fileInputRef} className='input-base p-1 mr-1' />
                <button
                  type='button'
                  onClick={handleDeleteImage}
                  className={
                    selectedCocktail.image === selectedCocktail.default_image
                      ? 'button-neutral p-2'
                      : 'button-danger p-2'
                  }
                  disabled={
                    selectedCocktail.image === selectedCocktail.default_image || selectedCocktail.id === undefined
                  }
                >
                  <FaTrashAlt />
                </button>
              </div>
            </form>
            <div className='flex-grow'></div>
            <div className='flex justify-between mt-2'>
              <button
                type='button'
                onClick={() => confirmAndExecute('Delete Cocktail', handleDelete)}
                className='button-danger-filled p-2 px-4 flex justify-between items-center'
              >
                <FaTrashAlt className='mr-2' />
                Delete
              </button>
              <button
                type='button'
                className={`p-2 px-4 flex justify-between items-center ${
                  isValidCocktail() ? 'button-primary-filled' : 'button-neutral-filled'
                }`}
                onClick={handlePost}
                disabled={!isValidCocktail()}
              >
                <FaPen className='mr-2' />
                {selectedCocktail?.id ? ' Apply' : ' Create'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default RecipeList;
