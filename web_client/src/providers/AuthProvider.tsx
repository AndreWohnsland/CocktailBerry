import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Tabs } from '../constants/tabs';
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

  // Use useMemo to prevent array recreation on every render
  const protectedManagementPaths = useMemo(() => {
    if (!config.UI_LOCKED_TABS) return [];
    return [
      config.UI_LOCKED_TABS[Tabs.Maker] ? '/cocktails' : '',
      config.UI_LOCKED_TABS[Tabs.Ingredients] ? '/manage/ingredients' : '',
      config.UI_LOCKED_TABS[Tabs.Recipes] ? '/manage/recipes' : '',
      config.UI_LOCKED_TABS[Tabs.Bottles] ? '/manage/bottles' : '',
    ].filter((path) => path !== '');
  }, [config.UI_LOCKED_TABS]);

  // Use refs to track previous auth state to avoid setState in effect
  const prevPathRef = useRef(location.pathname);

  // This effect intentionally sets state when navigating away from protected routes
  // to clear authentication. This is a valid use case for syncing with external navigation.
  useEffect(() => {
    const prevPath = prevPathRef.current;
    prevPathRef.current = location.pathname;

    // Only reset master auth when leaving options section
    if (prevPath.startsWith('/options') && !location.pathname.startsWith('/options') && masterAuthenticated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: clearing auth on route change
      setMasterAuthenticated(false);
      setMasterPassword(0);
    }
    // Only reset maker auth when leaving protected paths
    const wasOnProtectedPath = protectedManagementPaths.some((path) => prevPath.startsWith(path));
    const isOnProtectedPath = protectedManagementPaths.some((path) => location.pathname.startsWith(path));
    if (wasOnProtectedPath && !isOnProtectedPath && makerAuthenticated) {
      setMakerAuthenticated(false);
      setMakerPassword(0);
    }
  }, [location.pathname, masterAuthenticated, makerAuthenticated, protectedManagementPaths]);

  const contextValue = useMemo(
    () => ({
      masterAuthenticated,
      setMasterAuthenticated,
      makerAuthenticated,
      setMakerAuthenticated,
      masterPassword,
      setMasterPassword,
      makerPassword,
      setMakerPassword,
    }),
    [masterAuthenticated, makerAuthenticated, masterPassword, makerPassword],
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
