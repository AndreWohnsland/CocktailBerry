import { IconType } from 'react-icons';

export interface ButtonProps {
  label: string;
  style?: 'primary' | 'secondary' | 'primary-filled' | 'secondary-filled' | 'neutral' | 'neutral-filled';
  textSize?: 'sm' | 'md' | 'lg';
  icon?: IconType;
  iconSize?: number;
  className?: string;
  passive?: boolean;
  onClick?: () => void;
}
export const TileButton = ({
  label,
  style = 'primary',
  className,
  icon: Icon,
  iconSize = 20,
  textSize = 'sm',
  passive = false,
  ...props
}: ButtonProps) => {
  const textSizeClass = textSize === 'sm' ? 'text-md' : textSize === 'md' ? 'text-lg' : 'text-xl';
  const extraClasses = [passive && 'disabled', textSizeClass, className].filter(Boolean).join(' ');
  return (
    <button
      type='button'
      className={`button-${style} p-2 py-4 w-full flex justify-center items-center ${extraClasses}`}
      {...props}
    >
      {Icon && <Icon className={`mr-2`} size={iconSize} />}
      {label}
    </button>
  );
};
