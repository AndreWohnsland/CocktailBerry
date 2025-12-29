import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPen, FaPlus, FaTrashAlt, FaUpload } from 'react-icons/fa';
import { MdNoDrinks } from 'react-icons/md';
import Modal from 'react-modal';
import {
  deleteCocktail,
  deleteCocktailImage,
  enableAllRecipes,
  postCocktail,
  updateCocktail,
  uploadCocktailImage,
  useCocktails,
} from '../../api/cocktails';
import { useIngredients } from '../../api/ingredients';
import { Cocktail, CocktailInput } from '../../types/models';
import { confirmAndExecute, errorToast, executeAndShow } from '../../utils';
import CloseButton from '../common/CloseButton';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import TileButton from '../common/TileButton';

const RecipeList: React.FC = () => {
  const { data: cocktails, isLoading, error, refetch } = useCocktails(false, 10, false);
  const [selectedCocktail, setSelectedCocktail] = useState<CocktailInput | null>(null);
  const { data: ingredients, isLoading: ingredientsLoading, error: ingredientsError } = useIngredients();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();

  if (isLoading || ingredientsLoading) return <LoadingData />;
  if (error || ingredientsError) return <ErrorComponent text={error?.message ?? ingredientsError?.message} />;

  let displayedCocktails = cocktails?.sort((a, b) => a.name.localeCompare(b.name));
  if (search) {
    displayedCocktails = displayedCocktails?.filter(
      (cocktail) =>
        cocktail.name.toLowerCase().includes(search.toLowerCase()) ??
        cocktail.ingredients.some((ingredient) => ingredient.name.toLowerCase().includes(search.toLowerCase())),
    );
  }

  const handleCocktailClick = (cocktail: Cocktail) => {
    setSelectedCocktail({
      id: cocktail.id,
      name: cocktail.name,
      enabled: cocktail.enabled,
      virgin_available: cocktail.virgin_available,
      price_per_100_ml: cocktail.price_per_100_ml,
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
      price_per_100_ml: 0,
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
    const success = await confirmAndExecute(t('recipes.enableAllRecipes'), enableAllRecipes);
    if (success) {
      refetch();
    }
  };

  const handleUploadImage = async () => {
    if (!selectedCocktail?.id) {
      errorToast('Recipe needs to be created before uploading image.');
      return;
    }
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      errorToast('Please select a file before uploading.');
      return;
    }
    const success = await executeAndShow(() => uploadCocktailImage(selectedCocktail.id!, file));
    if (success) {
      refetch();
    }
  };

  const handleDeleteImage = async () => {
    if (!selectedCocktail?.id) return;
    const success = await confirmAndExecute(t('recipes.deleteExistingImage'), () =>
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
    const success = await confirmAndExecute(t('recipes.deleteRecipe'), () => deleteCocktail(cocktailId));
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

  const sortedIngredients = ingredients?.sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className='p-2 pt-0 w-full max-w-3xl'>
      <SearchBar search={search} setSearch={setSearch}></SearchBar>
      <div className='grid grid-cols-2 md:grid-cols-3 gap-4'>
        <div className='col-span-2 md:col-span-3 w-full flex flex-row gap-4'>
          <TileButton
            label={t('new')}
            style='secondary'
            filled
            textSize='lg'
            icon={FaPlus}
            iconSize={25}
            onClick={handleNewCocktailClick}
          />
          <TileButton
            label={t('recipes.enableAll')}
            style='neutral'
            filled
            textSize='lg'
            onClick={handleEnableAllRecipes}
          />
        </div>
        {displayedCocktails?.map((cocktail) => (
          <TileButton
            label={cocktail.name}
            icon={cocktail.virgin_available ? MdNoDrinks : undefined}
            onClick={() => handleCocktailClick(cocktail)}
            key={cocktail.id}
            passive={!cocktail.enabled}
          />
        ))}
      </div>

      <Modal isOpen={!!selectedCocktail} onRequestClose={closeModal} className='modal' overlayClassName='overlay z-20'>
        {selectedCocktail && (
          <div className='px-1 rounded w-full h-full flex flex-col'>
            <div className='flex justify-between items-center mb-2'>
              <p className='text-xl font-bold text-secondary'>{selectedCocktail.name ?? t('recipes.newRecipe')}</p>
              <CloseButton onClick={closeModal} />
            </div>
            <div className='flex-grow'></div>
            <form className='space-y-2 text-neutral grid-cols-2 grid h-xs:grid-cols-1'>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('recipes.name')}:</p>
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
                  <p className='pr-2'>{t('recipes.enabled')}:</p>
                  <input
                    type='checkbox'
                    name='enabled'
                    checked={selectedCocktail.enabled}
                    onChange={handleChange}
                    className='checkbox-large'
                  />
                </label>
                <label className='flex justify-center items-center'>
                  <p className='pr-2'>{t('recipes.virginAvailable')}:</p>
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
                    <option value={0} disabled>
                      {t('recipes.selectIngredient')}
                    </option>
                    {sortedIngredients?.map((ing) => (
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
                {t('recipes.addIngredient')}
              </button>
              <label className='flex justify-center items-center'>
                <p className='pr-2'>{t('recipes.price')}:</p>
                <input
                  type='number'
                  name='price_per_100_ml'
                  step='0.1'
                  value={selectedCocktail.price_per_100_ml}
                  onChange={handleChange}
                  className='input-base w-full p-2'
                />
                <p className='px-2'>€/100ml</p>
              </label>
              <div className='flex items-center pt-1'>
                <button
                  type='button'
                  onClick={handleUploadImage}
                  className={`${!selectedCocktail?.id && 'disabled'} p-2 mr-1 button-secondary`}
                >
                  <FaUpload />
                </button>
                <input type='file' accept='image/*' ref={fileInputRef} className='input-base p-1 mr-1' />
                <button
                  type='button'
                  onClick={handleDeleteImage}
                  className={`button-danger p-2 ${
                    selectedCocktail.image === selectedCocktail.default_image && 'disabled'
                  }`}
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
                onClick={handleDelete}
                disabled={!selectedCocktail?.id}
                className={`${
                  !selectedCocktail?.id && 'disabled'
                } p-2 px-4 flex justify-between items-center button-danger-filled`}
              >
                <FaTrashAlt className='mr-2' />
                {t('delete')}
              </button>
              <button
                type='button'
                className={`p-2 px-4 flex justify-between items-center button-primary-filled ${
                  !isValidCocktail() && 'disabled'
                }`}
                onClick={handlePost}
                disabled={!isValidCocktail()}
              >
                {selectedCocktail?.id ? <FaPen className='mr-2' /> : <FaPlus className='mr-2' />}
                {selectedCocktail?.id ? t('apply') : t('create')}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RecipeList;
