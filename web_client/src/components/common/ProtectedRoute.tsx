import React from 'react';
import { validateMakerPassword, validateMasterPassword } from '../../api/options';
import { useAuth } from '../../AuthProvider';
import { useConfig } from '../../providers/ConfigProvider';
import PasswordPage from './PasswordPage';

interface ProtectedRouteProps {
  children: React.ReactNode;
  setAuthenticated: (password: number) => void;
  passwordName: string;
  authMethod: (password: number) => Promise<{ message: string }>;
  isProtected?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  setAuthenticated,
  passwordName,
  authMethod,
  isProtected = true,
}) => {
  if (isProtected) {
    return <PasswordPage passwordName={passwordName} setAuthenticated={setAuthenticated} authMethod={authMethod} />;
  }

  return <>{children}</>;
};

interface MakerPasswordProtectedProps {
  children: React.ReactNode;
  tabNumber: number;
}

export const MakerPasswordProtected: React.FC<MakerPasswordProtectedProps> = ({ children, tabNumber }) => {
  const { config } = useConfig();
  const isProtected = config.UI_LOCKED_TABS[tabNumber];
  const { makerAuthenticated, setMakerAuthenticated, setMakerPassword } = useAuth();
  const hasPassword = config.UI_MAKER_PASSWORD;
  return (
    <ProtectedRoute
      isProtected={hasPassword && isProtected && !makerAuthenticated}
      setAuthenticated={(password: number) => {
        setMakerAuthenticated(true);
        setMakerPassword(password);
      }}
      passwordName='Maker'
      authMethod={validateMakerPassword}
    >
      {children}
    </ProtectedRoute>
  );
};

interface MasterPasswordProtectedProps {
  children: React.ReactNode;
}

export const MasterPasswordProtected: React.FC<MasterPasswordProtectedProps> = ({ children }) => {
  const { config } = useConfig();
  const { masterAuthenticated, setMasterAuthenticated, setMasterPassword } = useAuth();
  const hasPassword = config.UI_MASTERPASSWORD;
  return (
    <ProtectedRoute
      isProtected={hasPassword && !masterAuthenticated}
      setAuthenticated={(password: number) => {
        setMasterAuthenticated(true);
        setMasterPassword(password);
      }}
      passwordName='Master'
      authMethod={validateMasterPassword}
    >
      {children}
    </ProtectedRoute>
  );
};
