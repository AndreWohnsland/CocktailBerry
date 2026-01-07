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
    sessionStorage.getItem(STORE_PROMPTED) === 'true'
  );
  const [restrictedModeActive, setRestrictedModeActive] = useState<boolean>(
    sessionStorage.getItem(STORE_RESTRICTED) === 'true'
  );

  // Check if we need to prompt based on config
  const shouldPrompt = config.PAYMENT_ONLY_MAKER_TAB && !hasPrompted;

  useEffect(() => {
    // Store prompted state in sessionStorage
    if (hasPrompted) {
      sessionStorage.setItem(STORE_PROMPTED, 'true');
    }
  }, [hasPrompted]);

  useEffect(() => {
    // Store restricted mode state in sessionStorage
    sessionStorage.setItem(STORE_RESTRICTED, restrictedModeActive.toString());
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
