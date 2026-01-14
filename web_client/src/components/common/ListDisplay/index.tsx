import { FaPlus } from 'react-icons/fa';
import type { PossibleConfigValue } from '../../../types/models';
import CloseButton from '../CloseButton';

interface ListDisplayProps<T = PossibleConfigValue> {
  children: React.ReactNode[];
  defaultValue: T;
  immutable: boolean;
  onAdd?: (value: T) => void;
  onRemove?: (index: number) => void;
}

const ListDisplay = ({ children, defaultValue, immutable, onAdd, onRemove }: ListDisplayProps) => {
  return (
    <div className='flex flex-col items-center w-full'>
      {children.map((item, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: is always ordered here
        <div key={index} className='flex items-center mb-1 w-full'>
          <span className='mr-1 font-bold text-secondary min-w-4'>{index + 1}</span>
          {item}
          {!immutable && <CloseButton iconSize={33} onClick={() => onRemove?.(index)} />}
        </div>
      ))}
      {!immutable && (
        <button
          type='button'
          onClick={() => onAdd?.(defaultValue)}
          className='flex justify-center items-center mb-2 mt-1 p-1 button-neutral w-full'
        >
          <FaPlus size={20} />
          <span className='ml-2'>Add</span>
        </button>
      )}
    </div>
  );
};

export default ListDisplay;
