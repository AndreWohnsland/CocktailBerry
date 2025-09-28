import { IconType } from 'react-icons';

interface ButtonProps {
  label: string | number;
  style?: 'primary' | 'secondary' | 'neutral' | 'neutral';
  filled?: boolean;
  textSize?: 'sm' | 'md' | 'lg';
  icon?: IconType;
  iconSize?: number;
  className?: string;
  passive?: boolean;
  onClick?: () => void;
}
const Button = ({
  label,
  style = 'primary',
  className,
  icon: Icon,
  iconSize = 20,
  textSize = 'sm',
  passive = false,
  filled = false,
  ...props
}: ButtonProps) => {
  const textSizeClass = textSize === 'sm' ? 'text-md' : textSize === 'md' ? 'text-lg' : 'text-xl';
  const extraClasses = [`button-${style}${filled ? '-filled' : ''}`, passive && 'disabled', textSizeClass, className]
    .filter(Boolean)
    .join(' ');
  return (
    <button type='button' className={`p-2 flex items-center justify-center ${extraClasses}`} {...props}>
      {Icon && <Icon className={`mr-2`} size={iconSize} />}
      {label}
    </button>
  );
};

export default Button;
