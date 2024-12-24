import React, { createContext, useState, useContext, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useConfig } from './ConfigProvider';

interface AuthContextType {
  masterAuthenticated: boolean;
  makerAuthenticated: boolean;
  setMasterAuthenticated: (authenticated: boolean) => void;
  setMakerAuthenticated: (authenticated: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [masterAuthenticated, setMasterAuthenticated] = useState(false);
  const [makerAuthenticated, setMakerAuthenticated] = useState(false);
  const location = useLocation();
  const { config } = useConfig();
  // need to check which tabs are locked and as soon we leave those tabs set the authenticated state to false
  let protectedManagementPaths: string[] = [];
  if (config.UI_LOCKED_TABS) {
    protectedManagementPaths = [
      (config.UI_LOCKED_TABS as boolean[])[0] ? '/manage/ingredients' : '',
      (config.UI_LOCKED_TABS as boolean[])[1] ? '/manage/recipes' : '',
      (config.UI_LOCKED_TABS as boolean[])[2] ? '/manage/bottles' : '',
    ].filter((path) => path !== '');
  }

  useEffect(() => {
    if (!location.pathname.startsWith('/options') && masterAuthenticated) {
      setMasterAuthenticated(false);
    }
    if (!protectedManagementPaths.some((path) => location.pathname.startsWith(path)) && makerAuthenticated) {
      setMakerAuthenticated(false);
    }
  }, [
    location,
    masterAuthenticated,
    makerAuthenticated,
    setMasterAuthenticated,
    setMakerAuthenticated,
    protectedManagementPaths,
  ]);

  return (
    <AuthContext.Provider
      value={{ masterAuthenticated, makerAuthenticated, setMasterAuthenticated, setMakerAuthenticated }}
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
