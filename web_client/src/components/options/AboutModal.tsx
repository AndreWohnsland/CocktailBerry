import { useTranslation } from 'react-i18next';
import { FaExternalLinkAlt } from 'react-icons/fa';
import Modal from 'react-modal';
import type { AboutInfo } from '../../types/models';
import CloseButton from '../common/CloseButton';
import TextHeader from '../common/TextHeader';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
  aboutInfo: AboutInfo | undefined;
}

const AboutModal = ({ isOpen, onClose, aboutInfo }: AboutModalProps) => {
  const { t } = useTranslation();

  const formatText = (text: string) => {
    return text.split('\n').map((line, index) => (
      // biome-ignore lint/suspicious/noArrayIndexKey: Static text, no reordering
      <div key={index}>{line}</div>
    ));
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} className='modal medium' overlayClassName='overlay z-20'>
      <div className='flex flex-col justify-between h-full bg-background p-4 rounded-lg w-full relative'>
        <div className='flex justify-between items-start'>
          <TextHeader text={t('options.about')} subheader />
          <CloseButton onClick={onClose} />
        </div>
        <div className='flex-grow' />
        <div className='text-neutral text-center items-center leading-relaxed space-y-4'>
          {aboutInfo ? (
            formatText(
              t('options.aboutText', {
                version: aboutInfo.version,
                platform: aboutInfo.platform,
                pythonVersion: aboutInfo.python_version,
              }),
            )
          ) : (
            <span>Loading...</span>
          )}
        </div>
        <div className='flex-grow py-4' />
        <footer className='bg-background px-4 rounded-b-lg flex justify-center'>
          <span className='text-neutral mr-2'>{t('options.documentation')}</span>
          <a
            href='https://docs.cocktailberry.org'
            target='_blank'
            rel='noopener noreferrer'
            className='inline-flex items-center gap-2 text-primary hover:underline'
          >
            docs.cocktailberry.org
            <FaExternalLinkAlt size={16} />
          </a>
        </footer>
      </div>
    </Modal>
  );
};

export default AboutModal;
