import React from 'react';
import { Ingredient } from '../../types/models';

interface ListViewProps {
  ingredientList: Ingredient[];
  setSelected: React.Dispatch<React.SetStateAction<Ingredient[]>>;
  selected: Ingredient[];
}

const ListView: React.FC<ListViewProps> = ({ ingredientList, setSelected, selected }) => {
  const handleSelect = (ingredient: Ingredient) => {
    setSelected((prev) => (prev.includes(ingredient) ? prev.filter((i) => i !== ingredient) : [...prev, ingredient]));
  };

  return (
    <>
      <div className='h-full overflow-y-auto border-2 border-neutral rounded-md px-2 py-1'>
        {ingredientList.map((ingredient) => (
          <div
            key={ingredient.id}
            onClick={() => handleSelect(ingredient)}
            className={`cursor-pointer p-2 my-1 rounded border font-bold ${
              selected.includes(ingredient) ? 'text-background bg-secondary border-secondary' : 'border-transparent'
            }`}
          >
            {ingredient.name}
          </div>
        ))}
      </div>
    </>
  );
};

export default ListView;
