import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCog, FaExclamationTriangle } from 'react-icons/fa';
import Modal from 'react-modal';
import { getAboutInfo, updateSoftware } from '../../api/options';
import type { UpdateAvailability, UpdateVersion } from '../../types/models';
import { executeAndShow, isBackendUnreachable } from '../../utils';
import CloseButton from '../common/CloseButton';
import DropDown from '../common/DropDown';
import InfoScreen from '../common/InfoScreen';
import TextHeader from '../common/TextHeader';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  info: UpdateAvailability | undefined;
  currentVersion: string | undefined;
}

const POLL_INTERVAL_MS = 2000;
// one request must not outlive a few poll ticks, otherwise a backend that accepts but never
// answers during startup leaves sockets piling up
const POLL_REQUEST_TIMEOUT_MS = 5000;
// a major update may reinstall dependencies on a Pi, so give it room before nagging
const POLL_PATIENCE_MS = 5 * 60 * 1000;

// Default to the highest version that does not cross a major boundary (the safe
// step), falling back to the newest available version if only major bumps exist.
const pickDefault = (versions: UpdateVersion[]): string => {
  const nonMajor = versions.filter((v) => !v.is_major);
  const pool = nonMajor.length > 0 ? nonMajor : versions;
  return pool.at(-1)?.version ?? '';
};

const UpdateModal = ({ isOpen, onClose, info, currentVersion }: UpdateModalProps) => {
  const { t } = useTranslation();
  const [selected, setSelected] = useState('');
  // The version as it was when the update started. It has to be a snapshot: the live value from
  // useAboutInfo refetches once the backend answers again, and would then match what we poll for.
  const [restartingFrom, setRestartingFrom] = useState<string | null>(null);
  const [takesLong, setTakesLong] = useState(false);

  const versions = useMemo(() => info?.versions ?? [], [info]);

  useEffect(() => {
    if (versions.length > 0) setSelected(pickDefault(versions));
  }, [versions]);

  // The reported version only changes once the restarted backend re-reads it, so it is the one
  // signal that separates "still the old process" from "update is live".
  useEffect(() => {
    if (restartingFrom === null) return;
    const startedAt = Date.now();
    let stopped = false;
    const poll = async () => {
      try {
        const about = await getAboutInfo({ timeout: POLL_REQUEST_TIMEOUT_MS });
        if (!stopped && about.version !== restartingFrom) {
          // the web client was replaced along with the backend, so pick up the new build
          window.location.reload();
          return;
        }
      } catch {
        // backend is down mid-restart, that is the expected case while waiting
      }
      if (!stopped && Date.now() - startedAt > POLL_PATIENCE_MS) setTakesLong(true);
    };
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      stopped = true;
      clearInterval(interval);
    };
  }, [restartingFrom]);

  const selectedInfo = versions.find((v) => v.version === selected);

  const options = versions.map((v) => ({
    value: v.version,
    label: v.is_major ? `${v.version}  ⚠ ${t('options.update.major')}` : v.version,
  }));

  const handleUpdate = async () => {
    if (!selected) return;
    const applied = await executeAndShow(async () => {
      try {
        return await updateSoftware(selected);
      } catch (error) {
        // A backend that vanished mid-apply is restarting, not failing: the poll settles it.
        // Only a structured API error is a real failure.
        if (!isBackendUnreachable(error)) throw error;
        return { message: t('options.update.restarting') };
      }
    });
    if (applied) setRestartingFrom(currentVersion ?? '');
  };

  if (restartingFrom !== null) {
    return (
      <Modal isOpen={isOpen} className='modal medium' overlayClassName='overlay z-20'>
        <div className='flex flex-col items-center justify-center h-full bg-background p-4 rounded-lg w-full'>
          <InfoScreen
            icon={<FaCog className='animate-spin text-neutral' size={100} />}
            title={t('options.update.restarting')}
            description={takesLong ? t('options.update.takingLonger') : t('options.update.restartingDescription')}
            hint={t('skeletons.errorPersistInformation')}
            button={
              takesLong ? (
                <button
                  type='button'
                  className='button-primary-filled p-2 px-4'
                  onClick={() => window.location.reload()}
                >
                  {t('options.update.reloadNow')}
                </button>
              ) : undefined
            }
          />
        </div>
      </Modal>
    );
  }

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
            {selectedInfo && (
              <pre className='whitespace-pre-wrap text-sm text-neutral bg-primary/5 p-2 rounded max-h-60 overflow-y-auto'>
                {selectedInfo.release_notes || t('options.update.notesUnavailable', { version: selectedInfo.version })}
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
