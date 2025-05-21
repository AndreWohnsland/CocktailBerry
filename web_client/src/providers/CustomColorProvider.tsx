import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import defaultColor from '../defaults/defaultColor';
import { CustomColors } from '../types/models';
import { useConfig } from './ConfigProvider';

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
          primary: config?.CUSTOM_COLOR_PRIMARY ?? defaultColor.primary,
          secondary: config?.CUSTOM_COLOR_SECONDARY ?? defaultColor.secondary,
          background: config?.CUSTOM_COLOR_BACKGROUND ?? defaultColor.background,
          neutral: config?.CUSTOM_COLOR_NEUTRAL ?? defaultColor.neutral,
          danger: config?.CUSTOM_COLOR_DANGER ?? defaultColor.danger,
        }),
    ),
  );

  useEffect(() => {
    if (!config) {
      return;
    }
    setCustomColors({
      primary: config.CUSTOM_COLOR_PRIMARY ?? defaultColor.primary,
      secondary: config.CUSTOM_COLOR_SECONDARY ?? defaultColor.secondary,
      background: config.CUSTOM_COLOR_BACKGROUND ?? defaultColor.background,
      neutral: config.CUSTOM_COLOR_NEUTRAL ?? defaultColor.neutral,
      danger: config.CUSTOM_COLOR_DANGER ?? defaultColor.danger,
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
