import i18next from 'i18next';

export type ConfirmRequest = {
  message: string;
  yesLabel: string;
  noLabel: string;
  resolve: (value: boolean) => void;
};

let listener: ((request: ConfirmRequest) => void) | null = null;

export const registerConfirmListener = (cb: (request: ConfirmRequest) => void): void => {
  listener = cb;
};

export const unregisterConfirmListener = (): void => {
  listener = null;
};

export const confirm = (message: string, yesLabel?: string, noLabel?: string): Promise<boolean> => {
  const resolvedYes = yesLabel ?? i18next.t('yes');
  const resolvedNo = noLabel ?? i18next.t('no');
  return new Promise((resolve) => {
    if (listener) {
      listener({ message, yesLabel: resolvedYes, noLabel: resolvedNo, resolve });
    } else {
      resolve(globalThis.window.confirm(message));
    }
  });
};
