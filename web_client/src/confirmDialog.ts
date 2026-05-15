import i18next from 'i18next';

export type ConfirmRequest = {
  message: string;
  yesLabel: string;
  noLabel: string;
  resolve: (value: boolean) => void;
};

let listener: ((request: ConfirmRequest) => void) | null = null;
// Only one dialog can be shown at a time; queue overlapping calls so a second
// confirm() doesn't overwrite the first request and orphan its promise.
let isActive = false;
const queue: Array<() => void> = [];

export const registerConfirmListener = (cb: (request: ConfirmRequest) => void): void => {
  listener = cb;
};

export const unregisterConfirmListener = (): void => {
  listener = null;
};

const dispatch = (message: string, yesLabel: string, noLabel: string, resolve: (value: boolean) => void): void => {
  if (!listener) {
    resolve(globalThis.window.confirm(message));
    return;
  }
  isActive = true;
  listener({
    message,
    yesLabel,
    noLabel,
    resolve: (value) => {
      resolve(value);
      isActive = false;
      const next = queue.shift();
      next?.();
    },
  });
};

export const confirm = (message: string, yesLabel?: string, noLabel?: string): Promise<boolean> => {
  const resolvedYes = yesLabel ?? i18next.t('yes');
  const resolvedNo = noLabel ?? i18next.t('no');
  return new Promise((resolve) => {
    const fire = () => dispatch(message, resolvedYes, resolvedNo, resolve);
    if (isActive) {
      queue.push(fire);
    } else {
      fire();
    }
  });
};
