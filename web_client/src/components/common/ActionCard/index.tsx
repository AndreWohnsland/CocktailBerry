import { IconType } from 'react-icons';
import TextHeader from '../TextHeader';

interface ActionCardProps {
  header?: string;
  sections: string[];
  actionText?: string;
  onActionClick?: () => void;
  actionIcon?: IconType;
  actionStyle?: 'primary' | 'danger';
}

const ActionCard = ({
  header,
  sections,
  actionText,
  onActionClick,
  actionIcon: Icon,
  actionStyle = 'primary',
}: ActionCardProps) => {
  return (
    <div className='w-full mt-4 border rounded-lg border-neutral items-center justify-center flex flex-col p-2'>
      {header && <TextHeader text={header} subheader space={2} />}
      {sections.map((section, index) => (
        <p key={index} className='text-center text-primary'>
          {section}
        </p>
      ))}
      {onActionClick && (
        <button
          onClick={onActionClick}
          className={`button-${actionStyle}-filled p-2 mt-2 w-full items-center justify-center flex`}
        >
          {Icon && <span className='mr-3'>{<Icon size={22} />}</span>}
          {actionText}
        </button>
      )}
    </div>
  );
};

export default ActionCard;
