import { toast } from 'react-toastify';
import { Cocktail } from './types/models';

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

export const confirmAndExecute = async (message: string, executable: () => Promise<void | any>): Promise<boolean> => {
  const confirmation = window.confirm(message);
  if (confirmation) {
    return executeAndShow(executable);
  } else {
    return Promise.resolve(false);
  }
};

const extractErrorMessage = (error: any): string => {
  let errorMessage = error?.response?.data?.detail || error?.detail || error.message || error || 'An error occurred';
  if (typeof errorMessage === 'object') {
    errorMessage = JSON.stringify(errorMessage);
  }
  return errorMessage;
};

export const errorToast = (error: any, prefix?: string) => {
  let errorMessage = extractErrorMessage(error);
  const randomNumber = Math.floor(100000 + Math.random() * 900000);
  const prefixMessage = prefix ? `${prefix}: ` : '';
  toast(`${prefixMessage}${errorMessage}`, {
    toastId: `${prefix}-error-${randomNumber}`,
    pauseOnHover: false,
  });
};

export const executeAndShow = async (executable: () => Promise<any>): Promise<boolean> => {
  let info = '';
  let toastId = 'execute-show-info';
  let success = false;
  // add some random six digit number at it
  const randomNumber = Math.floor(100000 + Math.random() * 900000);
  await executable()
    .then((result) => {
      info = result?.message || result;
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

export const OPTIONTABS = ['UI', 'MAKER', 'HARDWARE', 'SOFTWARE', 'OTHER'];

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
};

/**
 * Determines if a given config belongs to a specific tab.
 * @param configName - The configuration name.
 * @param tab - The tab to check.
 * @returns True if the config belongs to the tab, false otherwise.
 */
export const isInCurrentTab = (configName: string, tab: string): boolean => {
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
