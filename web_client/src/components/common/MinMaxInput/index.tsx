import { FaMinus, FaPlus } from 'react-icons/fa';
import NumberInput from '../NumberInput';

interface MinMaxInputProps {
  value: number;
  onChange: (value: number) => void;
  max: number;
  min?: number;
  delta: number;
  className?: string;
}

const MinMaxInput = ({ value, onChange, max, min = 0, delta, className }: MinMaxInputProps) => {
  const adjust = (step: number) => {
    const newValue = Math.max(min, Math.min(max, value + step));
    const snapped = Math.round(newValue / Math.abs(step)) * Math.abs(step);
    onChange(Math.max(min, Math.min(max, snapped)));
  };

  return (
    <div className={`flex justify-center gap-2 ${className ?? ''}`}>
      <button type='button' className='button-primary p-2 h-full' onClick={() => onChange(min)}>
        Min
      </button>
      <button type='button' onClick={() => adjust(-delta)} className='button-primary p-2'>
        <FaMinus size={25} />
      </button>
      <NumberInput value={value} readOnly fillParent />
      <button type='button' onClick={() => adjust(delta)} className='button-primary p-2'>
        <FaPlus size={25} />
      </button>
      <button type='button' className='button-primary p-2 h-full' onClick={() => onChange(max)}>
        Max
      </button>
    </div>
  );
};

export default MinMaxInput;
