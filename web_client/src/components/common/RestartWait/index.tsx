import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { getAboutInfo, useAboutInfo } from '../../../api/options';
import { POLL_REQUEST_TIMEOUT_MS, usePolling } from '../../../hooks/usePolling';
import WaitModal from '../WaitModal';

interface RestartWaitProps {
  waiting: boolean;
  /** How long to wait before admitting this is slow and offering a manual reload. */
  patienceMs: number;
}

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
  // Read through a ref: the query refetches once the backend answers again, and that must not
  // restart the wait with the new process as its baseline.
  const lastSeen = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (about?.startup_time !== undefined) lastSeen.current = about.startup_time;
  }, [about?.startup_time]);

  const takesLong = usePolling(waiting, patienceMs, () => {
    // The cached value is the only one guaranteed to come from the process that is going down:
    // probing now can already hit the restarted one, which would make the baseline unreachable
    // and leave the wait spinning forever.
    let baseline = lastSeen.current;
    return async () => {
      let current: number | undefined;
      try {
        current = (await getAboutInfo({ timeout: POLL_REQUEST_TIMEOUT_MS })).startup_time;
      } catch {
        return false;
      }
      if (baseline === undefined) {
        // nothing known yet and the backend still answers: this is the process we wait to leave
        baseline = current;
      } else if (current !== baseline) {
        // the web client may have been replaced along with the backend, so take the new build
        window.location.reload();
        return true;
      }
      return false;
    };
  });

  return (
    <WaitModal
      open={waiting}
      title={t('restart.title')}
      description={t('restart.description')}
      takesLong={takesLong}
      takesLongText={t('restart.takingLonger')}
      hint={t('skeletons.errorPersistInformation')}
    />
  );
};

export default RestartWait;
