import type { IconType } from 'react-icons';

interface TextHeaderProps {
  text: string;
  subheader?: boolean;
  icon?: IconType;
  space?: number;
  huge?: boolean;
}

const TextHeader = ({ text, subheader, icon: Icon, space, huge }: TextHeaderProps) => {
  space = space ?? (subheader ? 4 : 8);
  return (
    <>
      {subheader ? (
        <h2 className={`text-secondary text-xl font-bold mb-${space} text-center flex items-center justify-center`}>
          {Icon && <Icon className={`mr-2`} />}
          {text}
        </h2>
      ) : (
        <h1
          className={`text-secondary text-${
            huge ? 4 : 2
          }xl font-bold mb-${space} text-center flex items-center justify-center`}
        >
          {Icon && <Icon className={`mr-2`} />}
          {text}
        </h1>
      )}
    </>
  );
};

export default TextHeader;
