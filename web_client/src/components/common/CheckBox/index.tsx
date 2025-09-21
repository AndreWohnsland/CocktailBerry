interface CheckBoxProps {
  value: boolean;
  checkName: string;
  handleInputChange: (value: boolean) => void;
}

const CheckBox = ({ value, checkName, handleInputChange }: CheckBoxProps) => {
  return (
    <>
      <label className='flex items-center'>
        <input
          type='checkbox'
          checked={value}
          onChange={(e) => handleInputChange(e.target.checked)}
          className='checkbox-large'
        />
        <span className='ml-2'>{checkName}</span>
      </label>
    </>
  );
};

export default CheckBox;
