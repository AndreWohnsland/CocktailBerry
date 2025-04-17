import React, { useState } from 'react';
import { MdNoDrinks } from 'react-icons/md';
import Modal from 'react-modal';
import { useCocktails } from '../../api/cocktails';
import { API_URL } from '../../api/common';
import { useConfig } from '../../ConfigProvider';
import { Cocktail } from '../../types/models';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import SearchBar from '../common/SearchBar';
import CocktailSelection from './CocktailSelection';
import SingleIngredientSelection from './SingleIngredientSelection';
import { useTranslation } from 'react-i18next';

const CocktailList: React.FC = () => {
  const { config } = useConfig();
  const { data: cocktails, error, isLoading } = useCocktails(true, config.MAKER_MAX_HAND_INGREDIENTS || 0);
  const [selectedCocktail, setSelectedCocktail] = useState<Cocktail | null>(null);
  const [singleIngredientOpen, setSingleIngredientOpen] = useState(false);
  const [search, setSearch] = useState('');
  const { t } = useTranslation();

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;

  const handleCocktailClick = (cocktail: Cocktail) => {
    setSelectedCocktail(cocktail);
  };

  const handleCloseModal = () => {
    setSelectedCocktail(null);
  };

  let displayedCocktails = cocktails;
  if (search) {
    displayedCocktails = displayedCocktails?.filter(
      (cocktail) =>
        cocktail.name.toLowerCase().includes(search.toLowerCase()) ||
        cocktail.ingredients.some((ingredient) => ingredient.name.toLowerCase().includes(search.toLowerCase())),
    );
  }

  return (
    <div className='px-2 centered max-w-7xl'>
      <SearchBar search={search} setSearch={setSearch}></SearchBar>
      <div className='flex flex-wrap gap-3 justify-center items-center w-full mb-4'>
        {displayedCocktails
          ?.sort((a, b) => a.name.localeCompare(b.name))
          .map((cocktail) => (
            <div
              key={cocktail.id}
              className='border-2 border-primary active:border-secondary rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold bg-primary active:bg-secondary text-background'
              onClick={() => handleCocktailClick(cocktail)}
              role='button'
            >
              <h2 className='text-center py-1 flex items-center justify-center'>
                {cocktail.virgin_available && (
                  <MdNoDrinks className={`mr-2 ${cocktail.only_virgin && 'border-2 border-background rounded-full'}`} />
                )}
                {cocktail.name}
              </h2>
              <div className='relative w-full' style={{ paddingTop: '100%' }}>
                <img
                  src={`${API_URL}${cocktail.image}`}
                  alt={cocktail.name}
                  className='absolute top-0 left-0 w-full h-full object-cover'
                />
              </div>
            </div>
          ))}
        {config.MAKER_ADD_SINGLE_INGREDIENT && (
          <div
            className='border-2 border-primary hover:border-secondary rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold bg-primary hover:bg-secondary text-background'
            onClick={() => setSingleIngredientOpen(true)}
            role='button'
          >
            <h2 className='text-center py-1 flex items-center justify-center'>{t('cocktails.singleIngredient')}</h2>
            <div className='relative w-full' style={{ paddingTop: '100%' }}>
              <img
                src={`${API_URL}/static/default/default.jpg`}
                alt='Single Ingredient'
                className='absolute top-0 left-0 w-full h-full object-cover'
              />
            </div>
          </div>
        )}
      </div>

      <Modal
        isOpen={!!selectedCocktail}
        onRequestClose={handleCloseModal}
        contentLabel='Cocktail Details'
        className='modal'
        overlayClassName='overlay z-20'
        preventScroll={true}
      >
        {selectedCocktail && (
          <CocktailSelection selectedCocktail={selectedCocktail} handleCloseModal={handleCloseModal} />
        )}
      </Modal>
      <Modal isOpen={singleIngredientOpen} className='modal slim' overlayClassName='overlay z-20' preventScroll={true}>
        <SingleIngredientSelection onClose={() => setSingleIngredientOpen(false)} />
      </Modal>
    </div>
  );
};

export default CocktailList;
