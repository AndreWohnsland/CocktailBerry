import React, { createContext, useState, useEffect, useContext } from 'react';
import { getConfigValues } from './api/options';
import { ConfigData } from './types/models';

interface IConfig {
  config: ConfigData;
  refetchConfig: () => Promise<void>;
}

const ConfigContext = createContext({} as IConfig);

export const ConfigProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<ConfigData>({});

  const fetchConfigValues = async () => {
    const configValues = await getConfigValues();
    setConfig(configValues);
  };

  useEffect(() => {
    fetchConfigValues();
  }, []);

  return (
    <ConfigContext.Provider
      value={{
        config,
        refetchConfig: fetchConfigValues,
      }}
    >
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = () => useContext(ConfigContext);
