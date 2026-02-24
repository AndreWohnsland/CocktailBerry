interface NumberInputBaseProps {
  value: number;
  prefix?: string;
  suffix?: string;
  id?: string;
  step?: number | string;
  className?: string;
  large?: boolean;
  fillParent?: boolean;
}

type NumberInputProps =
  | (NumberInputBaseProps & { readOnly: true; handleInputChange?: never })
  | (NumberInputBaseProps & { readOnly?: false; handleInputChange: (value: number) => void });

const NumberInput = ({
  value,
  prefix,
  suffix,
  id,
  step,
  readOnly,
  className,
  large = false,
  fillParent = false,
  handleInputChange,
}: NumberInputProps) => {
  return (
    <div className={`flex items-center whitespace-nowrap w-full ${className ?? ''}`}>
      {prefix && <span className='text-neutral mx-1 whitespace-nowrap'>{prefix}</span>}
      <input
        type='number'
        id={id}
        value={value.toString()}
        step={step}
        readOnly={readOnly}
        onChange={(e) => {
          const numericValue = Number.parseFloat(e.target.value);
          handleInputChange?.(Number.isNaN(numericValue) ? 0 : numericValue);
        }}
        className={`${large ? 'input-base-large' : 'input-base'} ${fillParent ? 'w-full h-full' : ''}`}
      />
      {suffix && <span className='text-neutral mx-1 whitespace-nowrap'>{suffix}</span>}
    </div>
  );
};

export default NumberInput;
