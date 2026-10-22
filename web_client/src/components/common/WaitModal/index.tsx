import { useTranslation } from 'react-i18next';
import { FaCog } from 'react-icons/fa';
import Modal from 'react-modal';
import InfoScreen from '../InfoScreen';

interface WaitModalProps {
  open: boolean;
  title: string;
  description: string;
  /** Shown instead of the description once the wait takes long, together with a manual reload. */
  takesLong: boolean;
  takesLongText: string;
  hint?: string;
}

/** Blocks the UI with a spinner while something outside the page finishes. */
const WaitModal = ({ open, title, description, takesLong, takesLongText, hint }: WaitModalProps) => {
  const { t } = useTranslation();
  if (!open) return null;

  return (
    <Modal isOpen className='modal medium' overlayClassName='overlay z-30'>
      <div className='flex flex-col items-center justify-center h-full bg-background p-4 rounded-lg w-full'>
        <InfoScreen
          icon={<FaCog className='animate-spin text-neutral' size={100} />}
          title={title}
          description={takesLong ? takesLongText : description}
          hint={hint}
          button={
            takesLong ? (
              <button type='button' className='button-primary-filled p-2 px-4' onClick={() => window.location.reload()}>
                {t('wait.reloadNow')}
              </button>
            ) : undefined
          }
        />
      </div>
    </Modal>
  );
};

export default WaitModal;
