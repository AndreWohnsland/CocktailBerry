import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCocktail, useCocktails } from '../../api/cocktails';
import { useConfig } from '../../providers/ConfigProvider';
import { Cocktail } from '../../types/models';
import ErrorComponent from '../common/ErrorComponent';
import LoadingData from '../common/LoadingData';
import CocktailSelection from './CocktailSelection';

const CocktailDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { config } = useConfig();
  const cocktailId = id ? parseInt(id, 10) : undefined;
  const { data: cocktail, error, isLoading } = useCocktail(cocktailId);
  const { data: allCocktails } = useCocktails(true, config.MAKER_MAX_HAND_INGREDIENTS ?? 0);
  const [selectedCocktail, setSelectedCocktail] = useState<Cocktail | undefined>(cocktail);

  useEffect(() => {
    if (cocktail) {
      setSelectedCocktail(cocktail);
    }
  }, [cocktail]);

  const handleCloseModal = useCallback(() => {
    navigate('/cocktails');
  }, [navigate]);

  const handleSetSelectedCocktail = useCallback(
    (cocktail: Cocktail) => {
      navigate(`/cocktails/${cocktail.id}`);
    },
    [navigate],
  );

  if (isLoading) return <LoadingData />;
  if (error) return <ErrorComponent text={error.message} />;
  if (!selectedCocktail) return <ErrorComponent text='Cocktail not found' />;

  return (
    <div className='px-2 centered max-w-7xl w-full h-full pt-4'>
      <div className='bg-background border-2 border-primary rounded-lg p-4 w-full h-full overflow-auto'>
        <CocktailSelection
          selectedCocktail={selectedCocktail}
          handleCloseModal={handleCloseModal}
          cocktails={allCocktails?.sort((a, b) => a.name.localeCompare(b.name)) || []}
          setSelectedCocktail={handleSetSelectedCocktail}
        />
      </div>
    </div>
  );
};

export default CocktailDetailPage;
