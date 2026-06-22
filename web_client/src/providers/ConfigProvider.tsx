import type React from 'react';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getBlacklist, getConfigValues } from '../api/options';
import type { Blacklist, DefinedConfigData, OptionTileName, OptionTiles } from '../types/models';

interface IConfig {
  config: DefinedConfigData;
  refetchConfig: () => Promise<void>;
  theme: string;
  changeTheme: (theme: string) => void;
  mode: Mode;
  toggleMode: () => void;
  blacklist: Blacklist;
  isConfigBlacklisted: (configName: string) => boolean;
  isTileBlacklisted: (tileName: OptionTileName) => boolean;
}

type Mode = 'light' | 'dark';

const STORE_THEME: string = 'THEME';
const STORE_MODE: string = 'MODE';
const STORE_CONFIG: string = 'CONFIG';
const STORE_BLACKLIST: string = 'BLACKLIST';

const EMPTY_OPTION_TILES: OptionTiles = {
  cleaning: false,
  configuration: false,
  calibration: false,
  scale_calibration: false,
  backup: false,
  restore: false,
  data: false,
  logs: false,
  wifi: false,
  addons: false,
  internet_check: false,
  update_system: false,
  update_software: false,
  system_resource_usage: false,
  about: false,
  news: false,
  sumup: false,
  waiters: false,
  events: false,
  reboot: false,
  shutdown: false,
  rfid: false,
  adjust_time: false,
  issues: false,
  recipe_calculation: false,
};
const EMPTY_BLACKLIST: Blacklist = { configs: [], options: EMPTY_OPTION_TILES };

const ConfigContext = createContext<IConfig | null>(null);

export const ConfigProvider = ({ children }: { children: React.ReactNode }) => {
  const [config, setConfig] = useState<DefinedConfigData>(JSON.parse(localStorage.getItem(STORE_CONFIG) ?? '{}'));
  const [theme, setTheme] = useState<string>(localStorage.getItem(STORE_THEME) ?? '');
  const [mode, setMode] = useState<Mode>(localStorage.getItem(STORE_MODE) === 'light' ? 'light' : 'dark');
  const [blacklist, setBlacklist] = useState<Blacklist>(
    JSON.parse(localStorage.getItem(STORE_BLACKLIST) ?? JSON.stringify(EMPTY_BLACKLIST)),
  );
  const { i18n } = useTranslation();

  const fetchConfigValues = useCallback(async () => {
    const configValues = await getConfigValues();
    const makerTheme = configValues.MAKER_THEME;
    if (makerTheme !== undefined) {
      setTheme(makerTheme.toString());
    }
    setConfig(configValues);
  }, []);

  const fetchBlacklist = useCallback(async () => {
    try {
      const data = await getBlacklist();
      setBlacklist(data);
    } catch {
      // public endpoint may briefly fail during startup; fall back to empty
      setBlacklist(EMPTY_BLACKLIST);
    }
  }, []);

  // Fetch config + blacklist on initial mount - this is intentional initialization
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: fetching initial config data on mount
    fetchConfigValues();
    fetchBlacklist();
  }, [fetchConfigValues, fetchBlacklist]);

  useEffect(() => {
    if (theme) {
      document.documentElement.className = theme;
      document.body.className = theme;
      localStorage.setItem(STORE_THEME, theme);
    }
  }, [theme]);

  // Apply Mode via the data-mode attribute. `custom` opts out of Mode (ADR 0003):
  // it is forced to dark so neither the light surface nor the text-darkening apply.
  // The user's stored Mode is preserved for when they switch back to a shipped Theme.
  useEffect(() => {
    const effectiveMode = theme === 'custom' ? 'dark' : mode;
    document.documentElement.setAttribute('data-mode', effectiveMode);
    document.body.setAttribute('data-mode', effectiveMode);
    localStorage.setItem(STORE_MODE, mode);
  }, [theme, mode]);

  useEffect(() => {
    localStorage.setItem(STORE_CONFIG, JSON.stringify(config));
    i18n.changeLanguage(config?.UI_LANGUAGE ?? 'en');
  }, [config, i18n]);

  useEffect(() => {
    localStorage.setItem(STORE_BLACKLIST, JSON.stringify(blacklist));
  }, [blacklist]);

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
  };

  const toggleMode = useCallback(() => setMode((m) => (m === 'dark' ? 'light' : 'dark')), []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: ignore handleThemeChange
  const contextValue = useMemo(
    () => ({
      config,
      refetchConfig: fetchConfigValues,
      theme,
      changeTheme: handleThemeChange,
      mode,
      toggleMode,
      blacklist,
      isConfigBlacklisted: (configName: string) => blacklist.configs.includes(configName),
      isTileBlacklisted: (tileName: OptionTileName) => blacklist.options[tileName],
    }),
    [config, theme, mode, toggleMode, fetchConfigValues, blacklist],
  );

  return <ConfigContext.Provider value={contextValue}>{children}</ConfigContext.Provider>;
};

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) throw new Error('useConfig must be used within a ConfigProvider');
  return context;
};
