import type { IconType } from 'react-icons';

// Literal class names: Tailwind only generates classes it can find as full strings in the source.
const SPACE_CLASS = { 0: 'mb-0', 2: 'mb-2', 4: 'mb-4', 8: 'mb-8' } as const;

interface TextHeaderProps {
  text: string;
  subheader?: boolean;
  icon?: IconType;
  space?: keyof typeof SPACE_CLASS;
  huge?: boolean;
}

const TextHeader = ({ text, subheader, icon: Icon, space, huge }: TextHeaderProps) => {
  const spaceClass = SPACE_CLASS[space ?? (subheader ? 4 : 8)];
  const content = (
    <>
      {Icon && <Icon className='mr-2' />}
      {text}
    </>
  );
  const base = `text-secondary font-bold ${spaceClass} text-center flex items-center justify-center`;
  return subheader ? (
    <h2 className={`${base} text-xl`}>{content}</h2>
  ) : (
    <h1 className={`${base} ${huge ? 'text-4xl' : 'text-2xl'}`}>{content}</h1>
  );
};

export default TextHeader;
