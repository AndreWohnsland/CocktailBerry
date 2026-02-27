import type React from 'react';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus, FaTrashAlt, FaUpload } from 'react-icons/fa';
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
import { useIngredients } from '../../api/ingredients';
import { useRestrictedMode } from '../../providers/RestrictedModeProvider';
import type { Cocktail, CocktailInput } from '../../types/models';
import { confirmAndExecute, errorToast, executeAndShow } from '../../utils';
import Button from '../common/Button';
import CheckBox from '../common/CheckBox';
import DropDown from '../common/DropDown';
import Modal from 'react-modal';
import CloseButton from '../common/CloseButton';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import ModalActions from '../common/ModalActions';
import NumberInput from '../common/NumberInput';
import SearchBar from '../common/SearchBar';
import TextInput from '../common/TextInput';
import TileButton from '../common/TileButton';

const RecipeList: React.FC = () => {
  const { data: cocktails, isLoading, error, refetch } = useCocktails(false, 10, false);
  const [selectedCocktail, setSelectedCocktail] = useState<CocktailInput | null>(null);
  const { data: ingredients, isLoading: ingredientsLoading, error: ingredientsError } = useIngredients();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();
  const { restrictedModeActive } = useRestrictedMode();

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

  const handleFieldChange = <K extends keyof CocktailInput>(name: K, value: CocktailInput[K]) => {
    setSelectedCocktail((prev) => prev && { ...prev, [name]: value });
  };

  const handleIngredientSelect = (index: number, value: string) => {
    setSelectedCocktail((prev) => {
      if (!prev) return null;
      const ingredients = [...prev.ingredients];
      ingredients[index] = { ...ingredients[index], id: Number(value) };
      return { ...prev, ingredients };
    });
  };

  const handleIngredientField = (index: number, field: 'amount' | 'recipe_order', value: number) => {
    setSelectedCocktail((prev) => {
      if (!prev) return null;
      const ingredients = [...prev.ingredients];
      ingredients[index] = { ...ingredients[index], [field]: value };
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
    // biome-ignore lint/style/noNonNullAssertion: will always be defined here
    const success = await executeAndShow(() => uploadCocktailImage(selectedCocktail.id!, file));
    if (success) {
      refetch();
    }
  };

  const handleDeleteImage = async () => {
    if (!selectedCocktail?.id) return;
    const success = await confirmAndExecute(t('recipes.deleteExistingImage'), () =>
      // biome-ignore lint/style/noNonNullAssertion: will always be defined here
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
    if (ingredients.length <= 0) return false;
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
      <SearchBar search={search} tabBarVisible={!restrictedModeActive} setSearch={setSearch}></SearchBar>
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
            <div className='flex-grow' />
            <form className='space-y-2 text-neutral grid-cols-2 grid h-xs:grid-cols-1'>
              <div className='flex justify-center items-center'>
                <TextInput
                  value={selectedCocktail.name}
                  handleInputChange={(value) => handleFieldChange('name', value)}
                  prefix={`${t('recipes.name')}:`}
                />
              </div>
              <div className='flex flex-row items-center w-full justify-center'>
                <div className='pr-4'>
                  <CheckBox
                    value={selectedCocktail.enabled}
                    checkName={t('recipes.enabled')}
                    handleInputChange={(value) => handleFieldChange('enabled', value)}
                  />
                </div>
                <CheckBox
                  value={selectedCocktail.virgin_available}
                  checkName={t('recipes.virginAvailable')}
                  handleInputChange={(value) => handleFieldChange('virgin_available', value)}
                />
              </div>
              {selectedCocktail.ingredients.map((ingredient, index) => (
                <div key={ingredient.id} className='flex items-center'>
                  <DropDown
                    value={ingredient.id ? ingredient.id.toString() : ''}
                    allowedValues={
                      sortedIngredients?.map((ing) => ({ value: ing.id.toString(), label: ing.name })) ?? []
                    }
                    handleInputChange={(value) => handleIngredientSelect(index, value)}
                    placeholder={t('recipes.selectIngredient')}
                    className='mr-2'
                  />
                  <NumberInput
                    value={ingredient.amount}
                    handleInputChange={(value) => handleIngredientField(index, 'amount', value)}
                    suffix='ml'
                  />
                  <NumberInput
                    value={ingredient.recipe_order}
                    handleInputChange={(value) => handleIngredientField(index, 'recipe_order', value)}
                    className='max-w-8'
                  />
                  <button type='button' onClick={() => removeIngredient(index)} className='button-danger p-2 ml-1'>
                    <FaTrashAlt />
                  </button>
                </div>
              ))}
              <Button style='neutral' icon={FaPlus} label={t('recipes.addIngredient')} onClick={addIngredient} />
              <NumberInput
                value={selectedCocktail.price_per_100_ml}
                handleInputChange={(value) => handleFieldChange('price_per_100_ml', value)}
                prefix={`${t('recipes.price')}:`}
                suffix='€/100ml'
                step={0.1}
              />
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
            <div className='flex-grow' />
            <div className='flex justify-between mt-2'>
              <ModalActions
                onDelete={handleDelete}
                onSave={handlePost}
                isNew={!selectedCocktail?.id}
                deleteDisabled={!selectedCocktail?.id}
                saveDisabled={!isValidCocktail()}
                deleteLabel={t('delete')}
                saveLabel={t('apply')}
                createLabel={t('create')}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RecipeList;
