import { useEffect, useRef, useState } from 'react';

const POLL_INTERVAL_MS = 2000;
// one request must not outlive a few poll ticks, otherwise a backend that accepts but never
// answers leaves sockets piling up
export const POLL_REQUEST_TIMEOUT_MS = 5000;

/**
 * Polls while `active`, until the step reports it is done. Returns whether the wait outlived
 * `patienceMs`, so the caller can admit it is slow.
 *
 * `makeStep` runs once per wait and returns the step, so state that must belong to one wait
 * (a baseline, a counter) lives in that closure instead of in refs the caller has to reset.
 */
export const usePolling = (active: boolean, patienceMs: number, makeStep: () => () => Promise<boolean>): boolean => {
  const [takesLong, setTakesLong] = useState(false);
  // read through a ref so a new closure per render does not restart the wait
  const makeStepRef = useRef(makeStep);
  makeStepRef.current = makeStep;

  useEffect(() => {
    if (!active) return;
    const startedAt = Date.now();
    const step = makeStepRef.current();
    let stopped = false;
    setTakesLong(false);

    let inFlight = false;
    const poll = async () => {
      if (inFlight) return; // a slow request must not let two ticks both finish the wait
      inFlight = true;
      const done = await step();
      inFlight = false;
      if (stopped) return;
      if (done) {
        stopped = true;
        clearInterval(interval);
        return;
      }
      if (Date.now() - startedAt > patienceMs) setTakesLong(true);
    };

    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      stopped = true;
      clearInterval(interval);
    };
  }, [active, patienceMs]);

  // the effect resets after paint, so without this a second wait flashes the previous slow state
  return active && takesLong;
};
