import type React from 'react';
import { createContext, useContext, useMemo, useState } from 'react';
import RestartWait from '../components/common/RestartWait';

interface IRestartWait {
  /** Block the UI until the backend comes back as a new process, then reload into it. */
  startRestartWait: (patienceMs: number) => void;
}

// Patience per kind of restart: a config change only re-execs, a software update may install
// dependencies on a Pi first, and a reboot waits on the whole machine.
export const RESTART_PATIENCE_MS = 60 * 1000;
export const UPDATE_PATIENCE_MS = 5 * 60 * 1000;
export const REBOOT_PATIENCE_MS = 2 * 60 * 1000;

const RestartWaitContext = createContext<IRestartWait | null>(null);

/**
 * Owns the restart wait so it outlives whatever triggered it.
 *
 * Mounted above the routes on purpose: the screens that start a restart gate themselves on their
 * own queries, which fail while the backend is down. Holding the modal inside one of them let an
 * error state unmount the very thing that was waiting for the backend to come back.
 *
 * There is no way to stop waiting, because every outcome ends in a reload.
 */
export const RestartWaitProvider = ({ children }: { children: React.ReactNode }) => {
  // the patience of the action being waited on, null when nothing is restarting
  const [patienceMs, setPatienceMs] = useState<number | null>(null);

  const contextValue = useMemo(() => ({ startRestartWait: setPatienceMs }), []);

  return (
    <RestartWaitContext.Provider value={contextValue}>
      {children}
      {/* always mounted: RestartWait remembers the startup time it last saw, which is the baseline
          it waits for the backend to leave behind. Remounting it would forget that. */}
      <RestartWait waiting={patienceMs !== null} patienceMs={patienceMs ?? 0} />
    </RestartWaitContext.Provider>
  );
};

export const useRestartWait = () => {
  const context = useContext(RestartWaitContext);
  if (!context) throw new Error('useRestartWait must be used within a RestartWaitProvider');
  return context;
};
