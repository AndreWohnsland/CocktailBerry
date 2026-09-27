import { useId } from 'react';

interface TextInputProps {
  value: string;
  label?: string;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  type?: 'text' | 'password';
  large?: boolean;
  className?: string;
  handleInputChange: (value: string) => void;
}

const TextInput = ({
  value,
  label,
  prefix,
  suffix,
  placeholder,
  type,
  large = false,
  className,
  handleInputChange,
}: TextInputProps) => {
  const id = useId();
  const inputRow = (
    <div className={`flex items-center whitespace-nowrap w-full ${label ? '' : (className ?? '')}`}>
      {prefix && <span className='text-neutral mx-1 whitespace-nowrap'>{prefix}</span>}
      <input
        id={id}
        type={type || 'text'}
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        className={large ? 'input-base-large' : 'input-base'}
        placeholder={placeholder}
      />
      {suffix && <span className='text-neutral mx-1 whitespace-nowrap'>{suffix}</span>}
    </div>
  );
  if (!label) return inputRow;
  return (
    <label htmlFor={id} className={`block w-full text-neutral text-center ${className ?? ''}`}>
      {label}
      {inputRow}
    </label>
  );
};

export default TextInput;
