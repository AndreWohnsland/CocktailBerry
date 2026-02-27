// components/IngredientList.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaPlus } from 'react-icons/fa';
import { IoHandLeft } from 'react-icons/io5';
import { deleteIngredient, postIngredient, updateIngredient, useIngredients } from '../../api/ingredients';
import { useRestrictedMode } from '../../providers/RestrictedModeProvider';
import type { Ingredient, IngredientInput } from '../../types/models';
import { confirmAndExecute, executeAndShow } from '../../utils';
import Modal from 'react-modal';
import CheckBox from '../common/CheckBox';
import CloseButton from '../common/CloseButton';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import ModalActions from '../common/ModalActions';
import NumberInput from '../common/NumberInput';
import SearchBar from '../common/SearchBar';
import TextInput from '../common/TextInput';
import TileButton from '../common/TileButton';

const IngredientList: React.FC = () => {
  const { data: ingredients, isLoading, error, refetch } = useIngredients();
  const [selectedIngredient, setSelectedIngredient] = useState<IngredientInput | null>(null);
  const [search, setSearch] = useState<string | null>(null);
  const { t } = useTranslation();
  const { restrictedModeActive } = useRestrictedMode();

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

  const updateField = <K extends keyof IngredientInput>(field: K, value: IngredientInput[K]) => {
    setSelectedIngredient((prev) => prev && { ...prev, [field]: value });
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
      <SearchBar search={search} tabBarVisible={!restrictedModeActive} setSearch={setSearch}></SearchBar>
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
            <div className='flex-grow' />
            <form className='space-y-2 text-neutral grid-cols-2 grid h-xs:grid-cols-1'>
              <div className='flex justify-center items-center'>
                <TextInput
                  prefix={`${t('ingredients.name')}:`}
                  value={selectedIngredient.name}
                  handleInputChange={(v) => updateField('name', v)}
                />
              </div>
              <NumberInput
                prefix={`${t('ingredients.alcohol')}:`}
                value={selectedIngredient.alcohol}
                handleInputChange={(v) => updateField('alcohol', v)}
              />
              <NumberInput
                prefix={`${t('ingredients.bottleVolume')}:`}
                value={selectedIngredient.bottle_volume}
                handleInputChange={(v) => updateField('bottle_volume', v)}
              />
              <NumberInput
                prefix={`${t('ingredients.cost')}:`}
                value={selectedIngredient.cost}
                handleInputChange={(v) => updateField('cost', v)}
              />
              <NumberInput
                prefix={`${t('ingredients.pumpSpeed')}:`}
                value={selectedIngredient.pump_speed}
                handleInputChange={(v) => updateField('pump_speed', v)}
              />
              <div className='flex justify-center items-center'>
                <TextInput
                  prefix={`${t('ingredients.unit')}:`}
                  value={selectedIngredient.unit}
                  handleInputChange={(v) => updateField('unit', v)}
                />
              </div>
              <div className='flex justify-center items-center col-span-2 h-xs:col-span-1'>
                <CheckBox
                  value={selectedIngredient.hand}
                  checkName={t('ingredients.onlyAddByHand')}
                  handleInputChange={(v) => updateField('hand', v)}
                />
              </div>
            </form>
            <div className='flex-grow' />
            <div className='flex justify-between mt-2'>
              <ModalActions
                onDelete={handleDelete}
                onSave={handlePost}
                isNew={!selectedIngredient?.id}
                deleteDisabled={!selectedIngredient?.id}
                saveDisabled={!isValidIngredient()}
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

export default IngredientList;
