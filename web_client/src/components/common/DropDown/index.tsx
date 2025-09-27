interface DropDownProps {
  value: string;
  allowedValues: string[] | Record<string, string>;
  handleInputChange: (value: string) => void;
  className?: string;
}

const DropDown = ({ value, allowedValues, handleInputChange, className }: DropDownProps) => {
  const options = Array.isArray(allowedValues)
    ? allowedValues.map((v) => ({ value: v, label: v }))
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
