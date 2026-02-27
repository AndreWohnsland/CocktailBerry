import Button from '../common/Button';
import { getServingSizeIconIndex, servingSizeIcons } from './utils';

interface ServingSizeButtonsProps {
  servingSizes: number[];
  onSelect: (amount: number) => void;
  getLabel?: (amount: number) => string | number;
  disabled?: boolean;
}

const ServingSizeButtons = ({ servingSizes, onSelect, getLabel, disabled }: ServingSizeButtonsProps) => {
  const sorted = [...servingSizes].sort((a, b) => a - b);
  return (
    <div className='flex justify-center items-end w-full mt-auto gap-2 sm:mb-0 mb-2'>
      {sorted.map((amount, index) => (
        <Button
          label={getLabel ? getLabel(amount) : amount}
          filled
          key={amount}
          onClick={() => onSelect(amount)}
          textSize='lg'
          className='w-full'
          icon={servingSizeIcons[getServingSizeIconIndex(index, sorted.length)]}
          iconSize={25}
          disabled={disabled}
        />
      ))}
    </div>
  );
};

export default ServingSizeButtons;
