import { FaMinus, FaPlus } from 'react-icons/fa';

interface StepperControlProps {
  value: number;
  onIncrement: () => void;
  onDecrement: () => void;
  unit?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeConfig = {
  sm: { iconSize: 20, padding: 'p-2', textSize: 'text-xl' },
  md: { iconSize: 25, padding: 'p-3', textSize: 'text-2xl' },
  lg: { iconSize: 30, padding: 'p-4', textSize: 'text-3xl' },
};

const StepperControl = ({ value, onIncrement, onDecrement, unit, size = 'md', className }: StepperControlProps) => {
  const { iconSize, padding, textSize } = sizeConfig[size];

  return (
    <div className={`flex items-center space-x-4 ${className ?? ''}`}>
      <button
        type='button'
        className={`button-primary ${padding} flex justify-center items-center`}
        onClick={onDecrement}
      >
        <FaMinus size={iconSize} />
      </button>
      <span className={`text-secondary ${textSize} min-w-[3ch] text-center`}>
        {value}
        {unit && <span className='text-neutral ml-1'>{unit}</span>}
      </span>
      <button
        type='button'
        className={`button-primary ${padding} flex justify-center items-center`}
        onClick={onIncrement}
      >
        <FaPlus size={iconSize} />
      </button>
    </div>
  );
};

export default StepperControl;
