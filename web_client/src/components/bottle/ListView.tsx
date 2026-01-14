import type React from 'react';
import type { Ingredient } from '../../types/models';

interface ListViewProps {
  ingredientList: Ingredient[];
  setSelected: React.Dispatch<React.SetStateAction<Ingredient[]>>;
  selected: Ingredient[];
}

const ListView: React.FC<ListViewProps> = ({ ingredientList, setSelected, selected }) => {
  const handleSelect = (ingredient: Ingredient) => {
    setSelected((prev) => (prev.includes(ingredient) ? prev.filter((i) => i !== ingredient) : [...prev, ingredient]));
  };

  // Sort ingredients: hand=true first, then by name alphabetically
  const sortedIngredients = [...ingredientList].sort((a, b) => {
    if (a.hand === b.hand) {
      return a.name.localeCompare(b.name);
    }
    return a.hand ? -1 : 1;
  });

  return (
    <div className='h-full overflow-y-auto border-2 border-neutral rounded-md px-2 py-1'>
      {sortedIngredients.map((ingredient) => (
        // biome-ignore lint/a11y/useFocusableInteractive: will use div for now
        // biome-ignore lint/a11y/useSemanticElements: will use div for now
        <div
          key={ingredient.id}
          onClick={() => handleSelect(ingredient)}
          className={`cursor-pointer p-2 my-1 rounded border font-bold ${
            selected.includes(ingredient) ? 'text-background bg-secondary border-secondary' : 'border-transparent'
          }`}
          role='button'
        >
          {ingredient.name}
        </div>
      ))}
    </div>
  );
};

export default ListView;
