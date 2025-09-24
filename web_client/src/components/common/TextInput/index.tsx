interface TextInputProps {
  value: string;
  prefix?: string;
  suffix?: string;
  handleInputChange: (value: string) => void;
}

const TextInput = ({ value, prefix, suffix, handleInputChange }: TextInputProps) => {
  return (
    <>
      {prefix && <span className='text-neutral mr-1'>{prefix}</span>}
      <input type='text' value={value} onChange={(e) => handleInputChange(e.target.value)} className='input-base' />
      {suffix && <span className='text-neutral ml-1'>{suffix}</span>}
    </>
  );
};

export default TextInput;
