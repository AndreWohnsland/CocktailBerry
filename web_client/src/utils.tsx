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

export const confirmAndExecute = async (message: string, executable: () => Promise<void | any>) => {
  const confirmation = window.confirm(`Do you want to ${message}?`);
  if (confirmation) {
    await executable().catch((error) => {
      const errorMessage = error?.response?.data?.detail || error.message || error;
      toast(`Error doing ${message}: ${errorMessage}`, {
        toastId: `${message}-error`,
        pauseOnHover: false,
      });
    });
  }
};

export const executeAndShow = async (executable: () => Promise<any>): Promise<Boolean> => {
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
      info = error?.response?.data?.detail || error.message || error;
      toastId = 'execute-show-error';
    });
  toast(info, {
    toastId: `${toastId}-${randomNumber}`,
    pauseOnHover: false,
  });
  return success;
};
