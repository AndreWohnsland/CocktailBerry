import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaExclamationTriangle } from 'react-icons/fa';
import Modal from 'react-modal';
import { updateSoftware } from '../../api/options';
import type { UpdateAvailability, UpdateVersion } from '../../types/models';
import { executeAndShow } from '../../utils';
import CloseButton from '../common/CloseButton';
import DropDown from '../common/DropDown';
import TextHeader from '../common/TextHeader';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  info: UpdateAvailability | undefined;
}

// Default to the highest version that does not cross a major boundary (the safe
// step), falling back to the newest available version if only major bumps exist.
const pickDefault = (versions: UpdateVersion[]): string => {
  const nonMajor = versions.filter((v) => !v.is_major);
  const pool = nonMajor.length > 0 ? nonMajor : versions;
  return pool[pool.length - 1]?.version ?? '';
};

const UpdateModal = ({ isOpen, onClose, info }: UpdateModalProps) => {
  const { t } = useTranslation();
  const [selected, setSelected] = useState('');

  const versions = useMemo(() => info?.versions ?? [], [info]);

  useEffect(() => {
    if (versions.length > 0) setSelected(pickDefault(versions));
  }, [versions]);

  const selectedInfo = versions.find((v) => v.version === selected);

  const options = versions.map((v) => ({
    value: v.version,
    label: v.is_major ? `${v.version}  ⚠ ${t('options.update.major')}` : v.version,
  }));

  const handleUpdate = async () => {
    if (!selected) return;
    const success = await executeAndShow(() => updateSoftware(selected));
    if (success) onClose();
  };

  return (
    <Modal isOpen={isOpen} onRequestClose={onClose} className='modal medium' overlayClassName='overlay z-20'>
      <div className='flex flex-col h-full bg-background p-4 rounded-lg w-full relative'>
        <div className='flex justify-between items-start'>
          <TextHeader text={t('options.update.title')} subheader />
          <CloseButton onClick={onClose} />
        </div>
        <div className='grow overflow-y-auto mt-2'>
          <div className='flex flex-col gap-3'>
            <p>{t('options.update.selectHint')}</p>
            <DropDown value={selected} allowedValues={options} handleInputChange={setSelected} />
            {selectedInfo?.is_major && (
              <div className='flex items-center gap-2 text-danger'>
                <FaExclamationTriangle />
                <span>{t('options.update.majorWarning')}</span>
              </div>
            )}
            {selectedInfo?.release_notes && (
              <pre className='whitespace-pre-wrap text-sm text-neutral bg-primary/5 p-2 rounded max-h-60 overflow-y-auto'>
                {selectedInfo.release_notes}
              </pre>
            )}
          </div>
        </div>
        <footer className='flex justify-end mt-4'>
          <button type='button' className='button-primary-filled p-2 px-4' onClick={handleUpdate} disabled={!selected}>
            {t('options.update.updateTo', { version: selected })}
          </button>
        </footer>
      </div>
    </Modal>
  );
};

export default UpdateModal;
