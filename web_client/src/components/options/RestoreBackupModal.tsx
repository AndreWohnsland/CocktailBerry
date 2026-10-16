import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaExclamationTriangle } from 'react-icons/fa';
import Modal from 'react-modal';
import { type BackupGroup, uploadBackup } from '../../api/options';
import { RESTART_PATIENCE_MS, useRestartWait } from '../../providers/RestartWaitProvider';
import { executeAndShow } from '../../utils';
import CheckBox from '../common/CheckBox';
import CloseButton from '../common/CloseButton';
import TextHeader from '../common/TextHeader';

interface RestoreBackupModalProps {
  file: File | null;
  onClose: () => void;
}

const ALL_GROUPS: BackupGroup[] = ['config', 'images', 'database'];

const RestoreBackupModal = ({ file, onClose }: RestoreBackupModalProps) => {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<BackupGroup[]>(ALL_GROUPS);
  const { startRestartWait } = useRestartWait();

  const toggle = (group: BackupGroup, checked: boolean) => {
    setSelected((current) => (checked ? [...current, group] : current.filter((g) => g !== group)));
  };

  const handleRestore = async () => {
    if (file === null || selected.length === 0) return;
    const restored = await executeAndShow(() => uploadBackup(file, selected));
    if (!restored) return;
    startRestartWait(RESTART_PATIENCE_MS);
    onClose();
  };

  return (
    <Modal isOpen={file !== null} onRequestClose={onClose} className='modal medium' overlayClassName='overlay z-20'>
      <div className='flex flex-col h-full bg-background p-4 rounded-lg w-full relative'>
        <div className='flex justify-between items-start'>
          <TextHeader text={t('options.restoreBackup.title')} subheader />
          <CloseButton onClick={onClose} />
        </div>
        <div className='grow overflow-y-auto mt-2'>
          <div className='flex flex-col items-center gap-3 text-center'>
            <p className='text-neutral'>{file?.name}</p>
            <div className='flex items-center gap-2 text-danger'>
              <FaExclamationTriangle size={28} />
              <span className='ml-2'>{t('options.restoreBackup.overwriteHint')}</span>
            </div>
            <div className='flex flex-col gap-3'>
              {ALL_GROUPS.map((group) => (
                <CheckBox
                  key={group}
                  value={selected.includes(group)}
                  checkName={t(`options.restoreBackup.${group}`)}
                  handleInputChange={(checked) => toggle(group, checked)}
                />
              ))}
            </div>
          </div>
        </div>
        <footer className='flex justify-between px-2 mt-4'>
          <button type='button' className='button-neutral min-w-36 px-2 py-2' onClick={onClose}>
            {t('cancel')}
          </button>
          <button
            type='button'
            className='button-primary-filled min-w-36 px-2 py-2'
            onClick={handleRestore}
            disabled={selected.length === 0}
          >
            {t('apply')}
          </button>
        </footer>
      </div>
    </Modal>
  );
};

export default RestoreBackupModal;
