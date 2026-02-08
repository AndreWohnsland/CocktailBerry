import { toast } from 'react-toastify';
import type { Cocktail, IssueData } from './types/models';

export const scaleCocktail = (cocktail: Cocktail, factor: number): Cocktail => {
  // Step 1: Adjust alcoholic ingredients to match the target alcohol percentage
  let totalAlcoholVolume = 0;
  let totalVolume = 0;

  const targetVolume = cocktail.amount;

  let ingredients = cocktail.ingredients.map((ingredient) => {
    if (ingredient.alcohol > 0) {
      const newVolume = ingredient.amount * factor;
      totalAlcoholVolume += newVolume * (ingredient.alcohol / 100);
      totalVolume += newVolume;
      return { ...ingredient, amount: newVolume };
    } else {
      totalVolume += ingredient.amount;
      return { ...ingredient };
    }
  });

  ingredients = ingredients.map((ingredient) => ({
    ...ingredient,
    amount: Math.round((ingredient.amount * targetVolume) / totalVolume),
  }));

  const newAlcoholPercent = (totalAlcoholVolume / targetVolume) * 100;

  return { ...cocktail, alcohol: Math.round(newAlcoholPercent), ingredients };
};

export const confirmAndExecute = async (message: string, executable: () => Promise<unknown>): Promise<boolean> => {
  const confirmation = globalThis.window.confirm(message);
  if (confirmation) {
    return executeAndShow(executable);
  } else {
    return false;
  }
};

const extractErrorMessage = (error: unknown): string => {
  const err = error as { response?: { data?: { detail?: string } }; detail?: string; message?: string };
  let errorMessage = err?.response?.data?.detail ?? err?.detail ?? err?.message ?? error ?? 'An error occurred';
  if (typeof errorMessage === 'object') {
    errorMessage = JSON.stringify(errorMessage);
  }
  return String(errorMessage);
};

export const errorToast = (error: unknown, prefix?: string) => {
  const errorMessage = extractErrorMessage(error);
  const randomNumber = Math.floor(100000 + Math.random() * 900000);
  const prefixMessage = prefix ? `${prefix}: ` : '';
  toast(`${prefixMessage}${errorMessage}`, {
    toastId: `${prefix}-error-${randomNumber}`,
    pauseOnHover: false,
  });
};

export const executeAndShow = async (executable: () => Promise<unknown>): Promise<boolean> => {
  let info = '';
  const toastId = 'execute-show-info';
  let success = false;
  // add some random six digit number at it
  const randomNumber = Math.floor(100000 + Math.random() * 900000);
  await executable()
    .then((result) => {
      const res = result as { message?: string };
      if (res?.message) {
        info = res.message;
      } else if (typeof result === 'object' && result !== null) {
        info = JSON.stringify(result);
      } else {
        info = String(result);
      }
      success = true;
    })
    .catch((error) => {
      info = extractErrorMessage(error);
    });
  toast(info, {
    toastId: `${toastId}-${randomNumber}`,
    pauseOnHover: false,
  });
  return success;
};

export const OPTIONTABS = ['UI', 'MAKER', 'HARDWARE', 'SOFTWARE', 'PAYMENT', 'OTHER'];

const exactSorting: { [key: string]: string[] } = {
  UI: [
    'MAKER_THEME',
    'CUSTOM_COLOR_PRIMARY',
    'CUSTOM_COLOR_SECONDARY',
    'CUSTOM_COLOR_NEUTRAL',
    'CUSTOM_COLOR_BACKGROUND',
    'CUSTOM_COLOR_DANGER',
  ],
  HARDWARE: ['MAKER_PUMP_REVERSION', 'MAKER_REVERSION_PIN', 'MAKER_PINS_INVERTED'],
};

const tabConfig: { [key: string]: string[] } = {
  UI: ['UI'],
  MAKER: ['MAKER'],
  HARDWARE: ['PUMP', 'LED', 'RFID'],
  SOFTWARE: ['MICROSERVICE', 'TEAM'],
  PAYMENT: ['PAYMENT'],
};

export const subTabConfig: {
  [key: string]: {
    [key: string]: string[];
  };
} = {
  PAYMENT: {
    CocktailBerry: [
      'PAYMENT_SHOW_NOT_POSSIBLE',
      'PAYMENT_LOCK_SCREEN_NO_USER',
      'PAYMENT_SERVICE_URL',
      'PAYMENT_SECRET_KEY',
      'PAYMENT_AUTO_LOGOUT_TIME_S',
      'PAYMENT_LOGOUT_AFTER_PREPARATION',
    ],
    SumUp: ['PAYMENT_SUMUP_API_KEY', 'PAYMENT_SUMUP_MERCHANT_CODE', 'PAYMENT_SUMUP_TERMINAL_ID'],
  },
};

const skipConfig = ['EXP_DEMO_MODE'];

/**
 * Determines if a given config belongs to a specific tab.
 * @param configName - The configuration name.
 * @param tab - The tab to check.
 * @returns True if the config belongs to the tab, false otherwise.
 */
export const isInCurrentTab = (configName: string, tab: string): boolean => {
  if (skipConfig.includes(configName)) {
    return false;
  }

  // Exclude configs that belong to a subTab
  const isInSubTab = Object.values(subTabConfig[tab] ?? {}).some((names) => names.includes(configName));
  if (isInSubTab) {
    return false;
  }

  if (exactSorting[tab]?.includes(configName)) {
    return true;
  }

  if (tabConfig[tab]?.some((prefix) => configName.toLowerCase().startsWith(prefix.toLowerCase()))) {
    // Ensure it isn't already handled by exactSorting
    const isInExactSorting = Object.keys(exactSorting).some((key) => exactSorting[key].includes(configName));
    return !isInExactSorting;
  }

  if (tab === 'OTHER') {
    const isInOtherTabs =
      Object.keys(exactSorting).some((key) => exactSorting[key].includes(configName)) ||
      Object.keys(tabConfig).some((key) =>
        tabConfig[key].some((prefix) => configName.toLowerCase().startsWith(prefix.toLowerCase())),
      );
    return !isInOtherTabs;
  }

  return false;
};

/**
 * Determines if a given config belongs to a specific sub-tab within a tab.
 * @param configName - The configuration name.
 * @param tab - The parent tab.
 * @param subTab - The sub-tab to check.
 * @returns True if the config belongs to the sub-tab, false otherwise.
 */
export const isInCurrentSubTab = (configName: string, tab: string, subTab: string): boolean => {
  return subTabConfig[tab]?.[subTab]?.includes(configName) ?? false;
};

export const hasStartupIssues = (issueData: IssueData | undefined): boolean => {
  if (!issueData) return false;
  return Object.values(issueData).some((issue) => issue.has_issue);
};

export const hastNotIgnoredStartupIssues = (issueData: IssueData | undefined): boolean => {
  if (!issueData) return false;
  return Object.values(issueData).some((issue) => issue.has_issue && !issue.ignored);
};
