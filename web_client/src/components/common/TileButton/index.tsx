import type { IconType } from 'react-icons';

interface TileButtonProps {
  label: string;
  style?: 'primary' | 'secondary' | 'neutral';
  filled?: boolean;
  textSize?: 'sm' | 'md' | 'lg';
  icon?: IconType;
  iconSize?: number;
  className?: string;
  passive?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}
const TileButton = ({
  label,
  style = 'primary',
  className,
  icon: Icon,
  iconSize = 20,
  textSize = 'sm',
  passive = false,
  disabled = false,
  filled = false,
  ...props
}: TileButtonProps) => {
  const textMapping = {
    sm: 'text-md',
    md: 'text-lg',
    lg: 'text-xl',
  };
  const textSizeClass = textMapping[textSize];
  const extraClasses = [
    `button-${style}${filled ? '-filled' : ''}`,
    passive && 'passive',
    disabled && 'disabled',
    textSizeClass,
    className,
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <button
      type='button'
      className={`p-2 py-4 w-full flex justify-center items-center ${extraClasses}`}
      disabled={disabled}
      {...props}
    >
      {Icon && <Icon className='mr-2' size={iconSize} />}
      {label}
    </button>
  );
};

export default TileButton;
