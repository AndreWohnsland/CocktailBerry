interface NumberInputProps {
  value: number;
  prefix?: string;
  suffix?: string;
  handleInputChange: (value: number) => void;
}

const NumberInput = ({ value, prefix, suffix, handleInputChange }: NumberInputProps) => {
  return (
    <div className='flex items-center whitespace-nowrap w-full'>
      {prefix && <span className='text-neutral mx-1 whitespace-nowrap'>{prefix}</span>}
      <input
        type='number'
        value={value.toString()}
        onChange={(e) => {
          const numericValue = Number.parseFloat(e.target.value);
          handleInputChange(Number.isNaN(numericValue) ? 0 : numericValue);
        }}
        className='input-base'
      />
      {suffix && <span className='text-neutral mx-1 whitespace-nowrap'>{suffix}</span>}
    </div>
  );
};

export default NumberInput;
