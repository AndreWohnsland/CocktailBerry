import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { getConfigValues } from './api/options';

interface ITheme {
  theme: string;
  onThemeChange: (theme: string) => void;
}

type Props = {
  children: ReactNode;
};

const ThemeContext = createContext({} as ITheme);
const STORE_CONSTANT: string = 'THEME';

export const ThemeProvider = ({ children }: Props) => {
  const [theme, setTheme] = useState<string>(localStorage.getItem(STORE_CONSTANT) || '');

  useEffect(() => {
    const initializeTheme = async () => {
      const configValues = await getConfigValues();
      const makerTheme = configValues.MAKER_THEME;
      if (makerTheme !== undefined) {
        setTheme(makerTheme.toString());
      }
    };

    initializeTheme();
  }, []);

  useEffect(() => {
    if (theme) {
      document.documentElement.className = theme;
      document.body.className = theme;
      localStorage.setItem(STORE_CONSTANT, theme);
    }
  }, [theme]);

  const handleChange = (newTheme: string) => {
    setTheme(newTheme);
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        onThemeChange: handleChange,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
