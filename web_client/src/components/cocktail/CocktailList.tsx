import React, { useState } from 'react';
import Modal from 'react-modal';
import { useCocktails } from '../../api/cocktails';
import { Cocktail } from '../../types/models';
import CocktailSelection from './CocktailSelection';
import { MdNoDrinks } from 'react-icons/md';

Modal.setAppElement('#root');

const CocktailList: React.FC = () => {
  const { data: cocktails, error, isLoading } = useCocktails();
  const [selectedCocktail, setSelectedCocktail] = useState<Cocktail | null>(null);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  const handleCocktailClick = (cocktail: Cocktail) => {
    setSelectedCocktail(cocktail);
  };

  const handleCloseModal = () => {
    setSelectedCocktail(null);
  };

  return (
    <div className='px-2 centered max-w-7xl'>
      <div className='flex flex-wrap gap-3 justify-center items-center w-full'>
        {cocktails?.map((cocktail) => (
          <div
            key={cocktail.id}
            className='border-2 border-primary hover:border-secondary rounded-xl box-border overflow-hidden min-w-56 max-w-64 basis-1 grow text-xl font-bold bg-primary hover:bg-secondary text-background'
            onClick={() => handleCocktailClick(cocktail)}
          >
            <h2 className='text-center py-1 flex items-center justify-center'>
              {cocktail.virgin_available && <MdNoDrinks className='mr-2' />}
              {cocktail.name}
            </h2>
            <div className='relative w-full' style={{ paddingTop: '100%' }}>
              <img
                src={`${import.meta.env.VITE_APP_API_URL}${cocktail.image}`}
                alt={cocktail.name}
                className='absolute top-0 left-0 w-full h-full object-cover'
              />
            </div>
          </div>
        ))}
      </div>

      {selectedCocktail && (
        <Modal
          isOpen={!!selectedCocktail}
          onRequestClose={handleCloseModal}
          contentLabel='Cocktail Details'
          className='modal'
          overlayClassName='overlay z-20'
          style={{
            content: {
              padding: '5px',
            },
          }}
        >
          <CocktailSelection selectedCocktail={selectedCocktail} handleCloseModal={handleCloseModal} />
        </Modal>
      )}
    </div>
  );
};

export default CocktailList;