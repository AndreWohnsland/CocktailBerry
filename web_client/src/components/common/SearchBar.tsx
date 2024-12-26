import React from 'react';
import { useTranslation } from 'react-i18next';
import { FaEraser, FaSearch } from 'react-icons/fa';

interface SearchBarProps {
  search: string;
  setSearch: (value: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ search, setSearch }) => {
  const [savedSearch, setSavedSearch] = React.useState(search);
  const [showSearch, setShowSearch] = React.useState(false);
  const { t } = useTranslation();

  const handleHideToggle = () => {
    if (showSearch) {
      setSavedSearch(search);
      setSearch('');
    } else {
      setSearch(savedSearch);
    }
    setShowSearch(!showSearch);
  };

  return (
    <div className='sticky-top mb-2 flex flex-row'>
      <div className='flex-grow'></div>
      <input
        type='text'
        placeholder={t('search')}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className='input-base mr-1 w-full p-3 max-w-sm'
        hidden={!showSearch}
      />
      <div hidden={!showSearch}>
        <button
          onClick={() => setSearch('')}
          className='button-neutral flex items-center justify-center p-2 mr-1 !border'
        >
          <FaEraser size={20} />
        </button>
      </div>
      <button
        onClick={handleHideToggle}
        className='button-primary flex items-center justify-center p-2 !border pointer-events-auto'
      >
        <FaSearch size={20} />
      </button>
    </div>
  );
};

export default SearchBar;
