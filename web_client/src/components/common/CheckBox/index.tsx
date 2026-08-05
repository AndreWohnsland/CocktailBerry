interface CheckBoxProps {
  value: boolean;
  checkName: string;
  handleInputChange: (value: boolean) => void;
  disabled?: boolean;
}

const CheckBox = ({ value, checkName, handleInputChange, disabled = false }: CheckBoxProps) => {
  return (
    <label className='flex items-center'>
      <input
        type='checkbox'
        checked={value}
        onChange={(e) => handleInputChange(e.target.checked)}
        className='checkbox-large'
        disabled={disabled}
      />
      <span className='ml-2'>{checkName}</span>
    </label>
  );
};

export default CheckBox;
