import type { IconType } from 'react-icons';

interface ButtonProps {
  label: string | number;
  style?: 'primary' | 'secondary' | 'neutral' | 'danger';
  filled?: boolean;
  textSize?: 'sm' | 'md' | 'lg';
  icon?: IconType;
  iconSize?: number;
  className?: string;
  passive?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}
const Button = ({
  label,
  style = 'primary',
  className,
  icon: Icon,
  iconSize = 20,
  textSize = 'sm',
  passive = false,
  disabled = false,
  filled = false,
  type = 'button',
  ...props
}: ButtonProps) => {
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
      type={type}
      className={`p-2 flex items-center justify-center ${extraClasses}`}
      disabled={disabled}
      {...props}
    >
      {Icon && <Icon className='mr-2' size={iconSize} />}
      {label}
    </button>
  );
};

export default Button;
