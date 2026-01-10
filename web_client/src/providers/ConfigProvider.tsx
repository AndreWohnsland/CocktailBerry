import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getConfigValues } from '../api/options';
import type { DefinedConfigData } from '../types/models';

interface IConfig {
  config: DefinedConfigData;
  refetchConfig: () => Promise<void>;
  theme: string;
  changeTheme: (theme: string) => void;
}

const STORE_THEME: string = 'THEME';
const STORE_CONFIG: string = 'CONFIG';
const ConfigContext = createContext({} as IConfig);

export const ConfigProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<DefinedConfigData>(JSON.parse(localStorage.getItem(STORE_CONFIG) ?? '{}'));
  const [theme, setTheme] = useState<string>(localStorage.getItem(STORE_THEME) ?? '');
  const { i18n } = useTranslation();

  const fetchConfigValues = useCallback(async () => {
    const configValues = await getConfigValues();
    const makerTheme = configValues.MAKER_THEME;
    if (makerTheme !== undefined) {
      setTheme(makerTheme.toString());
    }
    setConfig(configValues);
  }, []);

  // Fetch config on initial mount - this is intentional initialization
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: fetching initial config data on mount
    fetchConfigValues();
  }, [fetchConfigValues]);

  useEffect(() => {
    if (theme) {
      document.documentElement.className = theme;
      document.body.className = theme;
      localStorage.setItem(STORE_THEME, theme);
    }
  }, [theme]);

  useEffect(() => {
    localStorage.setItem(STORE_CONFIG, JSON.stringify(config));
    i18n.changeLanguage(config?.UI_LANGUAGE ?? 'en');
  }, [config, i18n]);

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
  };

  const contextValue = useMemo(
    () => ({
      config,
      refetchConfig: fetchConfigValues,
      theme,
      changeTheme: handleThemeChange,
    }),
    [config, theme, fetchConfigValues],
  );

  return <ConfigContext.Provider value={contextValue}>{children}</ConfigContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useConfig = () => useContext(ConfigContext);
