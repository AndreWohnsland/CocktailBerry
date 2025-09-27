interface TextInputProps {
  value: string;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  type?: 'text' | 'password';
  handleInputChange: (value: string) => void;
}

const TextInput = ({ value, prefix, suffix, placeholder, type, handleInputChange }: TextInputProps) => {
  return (
    <>
      {prefix && <span className='text-neutral mr-1'>{prefix}</span>}
      <input
        type={type || 'text'}
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        className='input-base'
        placeholder={placeholder}
      />
      {suffix && <span className='text-neutral ml-1'>{suffix}</span>}
    </>
  );
};

export default TextInput;
