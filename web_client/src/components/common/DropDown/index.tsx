interface DropDownProps {
  value: string;
  allowedValues: string[];
  handleInputChange: (value: string) => void;
}

const DropDown = ({ value, allowedValues, handleInputChange }: DropDownProps) => {
  return (
    <select value={value} onChange={(e) => handleInputChange(e.target.value)} className='select-base'>
      {allowedValues.map((allowedValue) => (
        <option key={allowedValue} value={allowedValue}>
          {allowedValue}
        </option>
      ))}
    </select>
  );
};

export default DropDown;
