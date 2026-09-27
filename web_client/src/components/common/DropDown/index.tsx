import { useId } from 'react';

interface DropDownOption {
  value: string;
  label: string;
}

interface DropDownProps {
  value: string;
  label?: string;
  allowedValues: string[] | Record<string, string> | DropDownOption[];
  handleInputChange: (value: string) => void;
  className?: string;
  id?: string;
  placeholder?: string;
}

const isDropDownOptionArray = (values: unknown[]): values is DropDownOption[] => {
  return (
    values.length > 0 &&
    typeof values[0] === 'object' &&
    values[0] !== null &&
    'value' in values[0] &&
    'label' in values[0]
  );
};

const DropDown = ({ value, label, allowedValues, handleInputChange, className, id, placeholder }: DropDownProps) => {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  let options: DropDownOption[];

  if (Array.isArray(allowedValues)) {
    if (isDropDownOptionArray(allowedValues)) {
      options = allowedValues;
    } else {
      options = allowedValues.map((v) => ({ value: v, label: v }));
    }
  } else {
    options = Object.entries(allowedValues).map(([val, label]) => ({ value: val, label }));
  }

  const select = (
    <select
      id={selectId}
      value={value}
      onChange={(e) => handleInputChange(e.target.value)}
      className={`select-base ${className ?? ''}`}
    >
      {placeholder && (
        <option value='' disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
  if (!label) return select;
  return (
    <label htmlFor={selectId} className='block w-full text-neutral text-center'>
      {label}
      {select}
    </label>
  );
};

export default DropDown;
