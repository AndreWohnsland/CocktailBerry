interface DropDownOption {
  value: string;
  label: string;
}

interface DropDownProps {
  value: string;
  allowedValues: string[] | Record<string, string> | DropDownOption[];
  handleInputChange: (value: string) => void;
  className?: string;
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

const DropDown = ({ value, allowedValues, handleInputChange, className }: DropDownProps) => {
  const options = Array.isArray(allowedValues)
    ? isDropDownOptionArray(allowedValues)
      ? allowedValues
      : allowedValues.map((v) => ({ value: v, label: v }))
    : Object.entries(allowedValues).map(([val, label]) => ({ value: val, label }));

  return (
    <select value={value} onChange={(e) => handleInputChange(e.target.value)} className={`select-base ${className}`}>
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
};

export default DropDown;
