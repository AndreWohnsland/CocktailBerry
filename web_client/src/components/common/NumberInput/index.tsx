interface NumberInputProps {
  value: number;
  prefix?: string;
  suffix?: string;
  handleInputChange: (value: number) => void;
}

const NumberInput = ({ value, prefix, suffix, handleInputChange }: NumberInputProps) => {
  return (
    <>
      {prefix && <span className='text-neutral mx-1'>{prefix}</span>}
      <input
        type='number'
        value={value.toString()}
        onChange={(e) => {
          const numericValue = parseFloat(e.target.value);
          handleInputChange(Number.isNaN(numericValue) ? 0 : numericValue);
        }}
        className='input-base'
      />
      {suffix && <span className='text-neutral mx-1'>{suffix}</span>}
    </>
  );
};

export default NumberInput;
