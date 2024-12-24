import React from 'react';
import { useConfig } from '../../ConfigProvider';
import { useAuth } from '../../AuthProvider';
import PasswordPage from './PasswordPage';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPassword: number;
  setAuthenticated: () => void;
  passwordName: string;
  isProtected?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPassword,
  setAuthenticated,
  passwordName,
  isProtected = true,
}) => {
  const needsPassword = isProtected && requiredPassword !== 0;

  if (needsPassword) {
    return (
      <PasswordPage
        requiredPassword={requiredPassword}
        passwordName={passwordName}
        setAuthenticated={setAuthenticated}
      />
    );
  }

  return <>{children}</>;
};

interface MakerPasswordProtectedProps {
  children: React.ReactNode;
  tabNumber: number;
}

export const MakerPasswordProtected: React.FC<MakerPasswordProtectedProps> = ({ children, tabNumber }) => {
  const { config } = useConfig();
  const isProtected = (config.UI_LOCKED_TABS as boolean[])[tabNumber];
  const { makerAuthenticated, setMakerAuthenticated } = useAuth();
  return (
    <ProtectedRoute
      requiredPassword={config.UI_MAKER_PASSWORD as number}
      isProtected={isProtected && !makerAuthenticated}
      setAuthenticated={() => setMakerAuthenticated(true)}
      passwordName='Maker Password'
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
  const { masterAuthenticated, setMasterAuthenticated } = useAuth();
  return (
    <ProtectedRoute
      requiredPassword={config.UI_MASTERPASSWORD as number}
      isProtected={!masterAuthenticated}
      setAuthenticated={() => setMasterAuthenticated(true)}
      passwordName='Master Password'
    >
      {children}
    </ProtectedRoute>
  );
};
