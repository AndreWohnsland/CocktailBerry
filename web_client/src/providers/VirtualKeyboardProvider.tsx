import type React from 'react';
import { lazy, Suspense } from 'react';
import { useConfig } from './ConfigProvider';

const VirtualKeyboard = lazy(() => import('./VirtualKeyboard'));

export const VirtualKeyboardProvider = ({ children }: { children: React.ReactNode }) => {
  const { config } = useConfig();
  const enabled = config?.UI_VIRTUAL_KEYBOARD === true;
  return (
    <>
      {children}
      {enabled && (
        <Suspense fallback={null}>
          <VirtualKeyboard />
        </Suspense>
      )}
    </>
  );
};
