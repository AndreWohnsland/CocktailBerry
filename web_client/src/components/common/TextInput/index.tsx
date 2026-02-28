interface TextInputProps {
  value: string;
  prefix?: string;
  suffix?: string;
  placeholder?: string;
  type?: 'text' | 'password';
  large?: boolean;
  handleInputChange: (value: string) => void;
}

const TextInput = ({ value, prefix, suffix, placeholder, type, large = false, handleInputChange }: TextInputProps) => {
  return (
    <div className='flex items-center whitespace-nowrap w-full'>
      {prefix && <span className='text-neutral mx-1 whitespace-nowrap'>{prefix}</span>}
      <input
        type={type || 'text'}
        value={value}
        onChange={(e) => handleInputChange(e.target.value)}
        className={large ? 'input-base-large' : 'input-base'}
        placeholder={placeholder}
      />
      {suffix && <span className='text-neutral mx-1 whitespace-nowrap'>{suffix}</span>}
    </div>
  );
};

export default TextInput;
