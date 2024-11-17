import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

interface ITheme {
  theme: string;
  onThemeChange: (theme: string) => void;
}

type Props = {
  children: ReactNode;
};

const ThemeContext = createContext({} as ITheme);
// const STORE_CONSTANT: string = 'THEME';

export const ThemeProvider = ({ children }: Props) => {
  const [theme, setTheme] = useState<string>('');

  useEffect(() => {
    document.documentElement.className = theme;
    document.body.className = theme;
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
