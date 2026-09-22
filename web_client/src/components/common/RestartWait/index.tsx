import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { FaCog } from 'react-icons/fa';
import Modal from 'react-modal';
import { getAboutInfo, useAboutInfo } from '../../../api/options';
import InfoScreen from '../InfoScreen';

interface RestartWaitProps {
  waiting: boolean;
  /** How long to wait before admitting this is slow and offering a manual reload. */
  patienceMs: number;
}

const POLL_INTERVAL_MS = 2000;
// one request must not outlive a few poll ticks, otherwise a backend that accepts but never
// answers during startup leaves sockets piling up
const POLL_REQUEST_TIMEOUT_MS = 5000;

/**
 * Blocks the UI while the backend goes down and comes back, then reloads into the fresh one.
 *
 * The backend reports a startup time that changes with the process, so waiting for it to differ
 * covers every flavour of restart (software update, config change, backup restore, reboot)
 * without the caller describing what it is waiting for.
 */
const RestartWait = ({ waiting, patienceMs }: RestartWaitProps) => {
  const { t } = useTranslation();
  const { data: about } = useAboutInfo();
  const [takesLong, setTakesLong] = useState(false);
  // Read through a ref: the query refetches once the backend answers again, and that must not
  // restart the wait with the new process as its baseline.
  const lastSeen = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (about?.startup_time !== undefined) lastSeen.current = about.startup_time;
  }, [about?.startup_time]);

  useEffect(() => {
    if (!waiting) return;
    const startedAt = Date.now();
    let stopped = false;
    setTakesLong(false);

    // The cached value is the only one guaranteed to come from the process that is going down:
    // probing now can already hit the restarted one, which would make the baseline unreachable
    // and leave the wait spinning forever.
    let baseline = lastSeen.current;

    const probe = async (): Promise<number | undefined> => {
      try {
        return (await getAboutInfo({ timeout: POLL_REQUEST_TIMEOUT_MS })).startup_time;
      } catch {
        return undefined;
      }
    };

    const poll = async () => {
      const current = await probe();
      if (stopped) return;
      if (current !== undefined) {
        if (baseline === undefined) {
          // nothing known yet and the backend still answers: this is the process we wait to leave
          baseline = current;
        } else if (current !== baseline) {
          // the web client may have been replaced along with the backend, so take the new build
          window.location.reload();
          return;
        }
      }
      if (Date.now() - startedAt > patienceMs) setTakesLong(true);
    };

    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      stopped = true;
      clearInterval(interval);
    };
  }, [waiting, patienceMs]);

  if (!waiting) return null;

  return (
    <Modal isOpen className='modal medium' overlayClassName='overlay z-30'>
      <div className='flex flex-col items-center justify-center h-full bg-background p-4 rounded-lg w-full'>
        <InfoScreen
          icon={<FaCog className='animate-spin text-neutral' size={100} />}
          title={t('restart.title')}
          description={takesLong ? t('restart.takingLonger') : t('restart.description')}
          hint={t('skeletons.errorPersistInformation')}
          button={
            takesLong ? (
              <button type='button' className='button-primary-filled p-2 px-4' onClick={() => window.location.reload()}>
                {t('restart.reloadNow')}
              </button>
            ) : undefined
          }
        />
      </div>
    </Modal>
  );
};

export default RestartWait;
