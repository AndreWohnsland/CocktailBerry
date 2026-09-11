import type { IconType } from 'react-icons';
import Button from '../Button';
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
    <div className='w-full mt-4 border rounded-lg items-center justify-center flex flex-col p-2'>
      {header && <TextHeader text={header} subheader space={2} />}
      {sections.map((section, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: Controlled here
        <p key={index} className='text-center text-primary wrap-break-word'>
          {section}
        </p>
      ))}
      {onActionClick && (
        <Button
          style={actionStyle}
          filled
          icon={Icon}
          iconSize={22}
          label={actionText ?? ''}
          className='mt-4 w-full'
          onClick={onActionClick}
        />
      )}
    </div>
  );
};

export default ActionCard;
