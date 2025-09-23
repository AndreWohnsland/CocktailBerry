interface ColorSelectProps {
  value: string;
  handleInputChange: (value: string) => void;
}

const ColorSelect = ({ value, handleInputChange }: ColorSelectProps) => {
  return (
    <div className='flex flex-row items-center w-full'>
      <input
        type='color'
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        className='w-full min-w-6'
      />
      <span className='ml-2 w-20 text-neutral'>{value}</span>
    </div>
  );
};

export default ColorSelect;
