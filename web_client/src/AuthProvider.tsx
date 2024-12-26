import React, { createContext, useState, useContext, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useConfig } from './ConfigProvider';

interface AuthContextType {
  masterAuthenticated: boolean;
  setMasterAuthenticated: (authenticated: boolean) => void;
  makerAuthenticated: boolean;
  setMakerAuthenticated: (authenticated: boolean) => void;
  masterPassword: number;
  setMasterPassword: (password: number) => void;
  makerPassword: number;
  setMakerPassword: (password: number) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [masterAuthenticated, setMasterAuthenticated] = useState(false);
  const [masterPassword, setMasterPassword] = useState(0);
  const [makerAuthenticated, setMakerAuthenticated] = useState(false);
  const [makerPassword, setMakerPassword] = useState(0);
  const location = useLocation();
  const { config } = useConfig();
  // need to check which tabs are locked and as soon we leave those tabs set the authenticated state to false
  let protectedManagementPaths: string[] = [];
  if (config.UI_LOCKED_TABS) {
    protectedManagementPaths = [
      config.UI_LOCKED_TABS[0] ? '/manage/ingredients' : '',
      config.UI_LOCKED_TABS[1] ? '/manage/recipes' : '',
      config.UI_LOCKED_TABS[2] ? '/manage/bottles' : '',
    ].filter((path) => path !== '');
  }

  useEffect(() => {
    if (!location.pathname.startsWith('/options') && masterAuthenticated) {
      setMasterAuthenticated(false);
      setMasterPassword(0);
    }
    if (!protectedManagementPaths.some((path) => location.pathname.startsWith(path)) && makerAuthenticated) {
      setMakerAuthenticated(false);
      setMakerPassword(0);
    }
  }, [location, masterAuthenticated, makerAuthenticated, protectedManagementPaths]);

  return (
    <AuthContext.Provider
      value={{
        masterAuthenticated,
        setMasterAuthenticated,
        makerAuthenticated,
        setMakerAuthenticated,
        masterPassword,
        setMasterPassword,
        makerPassword,
        setMakerPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
