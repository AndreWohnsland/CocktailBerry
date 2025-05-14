import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useConfig } from './ConfigProvider';
import { CustomColors } from './types/models';

interface ICustomColor {
  customColors: CustomColors;
  setCustomColors: (colors: CustomColors) => void;
}

const STORE_CUSTOM_COLOR: string = 'COLORS';
const CustomColorContext = createContext({} as ICustomColor);

export const CustomColorProvider = ({ children }: { children: React.ReactNode }) => {
  const { theme, config } = useConfig();
  const [customColors, setCustomColors] = useState<CustomColors>(
    JSON.parse(
      localStorage.getItem(STORE_CUSTOM_COLOR) ??
        JSON.stringify({
          primary: config?.CUSTOM_COLOR_PRIMARY ?? '#007bff',
          secondary: config?.CUSTOM_COLOR_SECONDARY ?? '#ef9700',
          background: config?.CUSTOM_COLOR_BACKGROUND ?? '#0d0d0d',
          neutral: config?.CUSTOM_COLOR_NEUTRAL ?? '#96adba',
          danger: config?.CUSTOM_COLOR_DANGER ?? '#d00000',
        }),
    ),
  );

  useEffect(() => {
    if (!config) {
      return;
    }
    setCustomColors({
      primary: config.CUSTOM_COLOR_PRIMARY ?? '#007bff',
      secondary: config.CUSTOM_COLOR_SECONDARY ?? '#ef9700',
      background: config.CUSTOM_COLOR_BACKGROUND ?? '#0d0d0d',
      neutral: config.CUSTOM_COLOR_NEUTRAL ?? '#96adba',
      danger: config.CUSTOM_COLOR_DANGER ?? '#d00000',
    });
  }, [config]);

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

export const useCustomColor = () => useContext(CustomColorContext);
