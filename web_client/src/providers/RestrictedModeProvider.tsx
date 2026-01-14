import type React from 'react';
import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useConfig } from './ConfigProvider';

interface IRestrictedMode {
  restrictedModeActive: boolean;
  hasPrompted: boolean;
  setRestrictedMode: (active: boolean) => void;
}

const STORE_PROMPTED: string = 'RESTRICTED_MODE_PROMPTED';
const STORE_RESTRICTED: string = 'RESTRICTED_MODE_ACTIVE';
const RestrictedModeContext = createContext({} as IRestrictedMode);

export const RestrictedModeProvider = ({ children }: { children: React.ReactNode }) => {
  const { config } = useConfig();
  const [hasPrompted, setHasPrompted] = useState<boolean>(localStorage.getItem(STORE_PROMPTED) === 'true');
  const [restrictedModeActive, setRestrictedModeActive] = useState<boolean>(
    localStorage.getItem(STORE_RESTRICTED) === 'true',
  );

  // Track the previous feature enabled state
  const prevFeatureEnabledRef = useRef<boolean | undefined>(undefined);

  useEffect(() => {
    const featureEnabled = config?.UI_ONLY_MAKER_TAB ?? false;
    const prevEnabled = prevFeatureEnabledRef.current;
    prevFeatureEnabledRef.current = featureEnabled;

    // Only reset when feature transitions from enabled to disabled
    if (prevEnabled === true && !featureEnabled) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: resetting state when feature is disabled
      setRestrictedModeActive(false);
      setHasPrompted(false);
      localStorage.removeItem(STORE_PROMPTED);
      localStorage.removeItem(STORE_RESTRICTED);
    }
  }, [config?.UI_ONLY_MAKER_TAB]);

  const shouldPrompt = (config?.UI_ONLY_MAKER_TAB ?? false) && !hasPrompted;

  useEffect(() => {
    if (hasPrompted) {
      localStorage.setItem(STORE_PROMPTED, hasPrompted.toString());
    }
  }, [hasPrompted]);

  useEffect(() => {
    if (restrictedModeActive) {
      localStorage.setItem(STORE_RESTRICTED, restrictedModeActive.toString());
    } else {
      localStorage.removeItem(STORE_RESTRICTED);
    }
  }, [restrictedModeActive]);

  const handleSetRestrictedMode = (active: boolean) => {
    setRestrictedModeActive(active);
    setHasPrompted(true);
  };

  // biome-ignore lint/correctness/useExhaustiveDependencies: handleSetRestrictedMode ignored here
  const contextValue = useMemo(
    () => ({
      restrictedModeActive,
      hasPrompted: hasPrompted || !shouldPrompt,
      setRestrictedMode: handleSetRestrictedMode,
    }),
    [restrictedModeActive, hasPrompted, shouldPrompt],
  );

  return <RestrictedModeContext.Provider value={contextValue}>{children}</RestrictedModeContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useRestrictedMode = () => useContext(RestrictedModeContext);
