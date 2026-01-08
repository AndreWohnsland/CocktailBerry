import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
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
  const [hasPrompted, setHasPrompted] = useState<boolean>(
    localStorage.getItem(STORE_PROMPTED) === 'true'
  );
  const [restrictedModeActive, setRestrictedModeActive] = useState<boolean>(
    localStorage.getItem(STORE_RESTRICTED) === 'true'
  );

  // React to config changes - if feature is disabled, reset restricted mode
  useEffect(() => {
    const featureEnabled = config?.PAYMENT_ONLY_MAKER_TAB ?? false;
    
    if (!featureEnabled) {
      // Config disabled - clear restricted mode and reset prompts
      setRestrictedModeActive(false);
      setHasPrompted(false);
      localStorage.removeItem(STORE_PROMPTED);
      localStorage.removeItem(STORE_RESTRICTED);
    }
  }, [config?.PAYMENT_ONLY_MAKER_TAB]);

  // Check if we need to prompt based on config
  const shouldPrompt = (config?.PAYMENT_ONLY_MAKER_TAB ?? false) && !hasPrompted;

  useEffect(() => {
    // Sync prompted state to localStorage
    if (hasPrompted) {
      localStorage.setItem(STORE_PROMPTED, hasPrompted.toString());
    }
  }, [hasPrompted]);

  useEffect(() => {
    // Store restricted mode state in localStorage
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

  const contextValue = useMemo(
    () => ({
      restrictedModeActive,
      hasPrompted: hasPrompted || !shouldPrompt,
      setRestrictedMode: handleSetRestrictedMode,
    }),
    [restrictedModeActive, hasPrompted, shouldPrompt]
  );

  return <RestrictedModeContext.Provider value={contextValue}>{children}</RestrictedModeContext.Provider>;
};

export const useRestrictedMode = () => useContext(RestrictedModeContext);
