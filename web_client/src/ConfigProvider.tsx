import React, { createContext, useState, useEffect, useContext } from 'react';
import { getConfigValues } from './api/options';
import { ConfigData } from './types/models';

interface IConfig {
  config: ConfigData;
  refetchConfig: () => Promise<void>;
  theme: string;
  changeTheme: (theme: string) => void;
}

const STORE_CONSTANT: string = 'THEME';
const ConfigContext = createContext({} as IConfig);

export const ConfigProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<ConfigData>({});
  const [theme, setTheme] = useState<string>(localStorage.getItem(STORE_CONSTANT) || '');

  const fetchConfigValues = async () => {
    const configValues = await getConfigValues();
    const makerTheme = configValues.MAKER_THEME;
    if (makerTheme !== undefined) {
      setTheme(makerTheme.toString());
    }
    setConfig(configValues);
  };

  useEffect(() => {
    fetchConfigValues();
  }, []);

  useEffect(() => {
    if (theme) {
      document.documentElement.className = theme;
      document.body.className = theme;
      localStorage.setItem(STORE_CONSTANT, theme);
    }
  }, [theme]);

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
  };

  return (
    <ConfigContext.Provider
      value={{
        config,
        refetchConfig: fetchConfigValues,
        theme,
        changeTheme: handleThemeChange,
      }}
    >
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => useContext(ConfigContext);
