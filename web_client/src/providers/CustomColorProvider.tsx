import type React from 'react';
import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import defaultColor from '../defaults/defaultColor';
import type { CustomColors, DefinedConfigData } from '../types/models';
import { useConfig } from './ConfigProvider';

interface ICustomColor {
  customColors: CustomColors;
  setCustomColors: (colors: CustomColors) => void;
}

const STORE_CUSTOM_COLOR: string = 'COLORS';
const CustomColorContext = createContext({} as ICustomColor);

// Helper to get colors from config or defaults
const getColorsFromConfig = (config: DefinedConfigData | undefined): CustomColors => ({
  primary: config?.CUSTOM_COLOR_PRIMARY ?? defaultColor.primary,
  secondary: config?.CUSTOM_COLOR_SECONDARY ?? defaultColor.secondary,
  background: config?.CUSTOM_COLOR_BACKGROUND ?? defaultColor.background,
  neutral: config?.CUSTOM_COLOR_NEUTRAL ?? defaultColor.neutral,
  danger: config?.CUSTOM_COLOR_DANGER ?? defaultColor.danger,
});

export const CustomColorProvider = ({ children }: { children: React.ReactNode }) => {
  const { theme, config } = useConfig();

  // Derive colors from config using useMemo instead of useEffect + setState
  const configColors = useMemo(() => getColorsFromConfig(config), [config]);

  const [customColors, setCustomColors] = useState<CustomColors>(() => {
    const stored = localStorage.getItem(STORE_CUSTOM_COLOR);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return configColors;
      }
    }
    return configColors;
  });

  // Sync customColors when config changes - intentional external state sync
  useEffect(() => {
    if (config) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: syncing colors with config from API
      setCustomColors(configColors);
    }
  }, [config, configColors]);

  useEffect(() => {
    localStorage.setItem(STORE_CUSTOM_COLOR, JSON.stringify(customColors));
  }, [customColors]);

  useEffect(() => {
    const root = document.documentElement;

    if (theme === 'custom') {
      Object.entries(customColors).forEach(([key, value]) => {
        root.style.setProperty(`--${key}-color`, value);
      });
    } else {
      // Reset variables to let CSS file handle them
      root.removeAttribute('style');
    }
  }, [theme, customColors]);

  const contextValue = useMemo(
    () => ({
      customColors,
      setCustomColors,
    }),
    [customColors],
  );

  return <CustomColorContext.Provider value={contextValue}>{children}</CustomColorContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useCustomColor = () => useContext(CustomColorContext);
