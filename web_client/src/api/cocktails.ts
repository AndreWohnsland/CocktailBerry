import { useQuery, UseQueryResult } from 'react-query';
import { Cocktail, CocktailInput, CocktailStatus, Ingredient } from '../types/models';
import { axiosInstance } from './common';

const cocktail_url = '/cocktails';

export const fetchCocktails = async (
  only_possible: boolean = true,
  max_hand_add: number = 3,
  scale: boolean = true,
): Promise<Cocktail[]> => {
  return axiosInstance
    .get<Cocktail[]>(cocktail_url, {
      params: {
        only_possible,
        max_hand_add,
        scale,
      },
    })
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error fetching cocktails:', error);
      return [];
    });
};

export const useCocktails = (
  only_possible: boolean = true,
  max_hand_add: number = 3,
  scale: boolean = true,
): UseQueryResult<Cocktail[], Error> => {
  return useQuery<Cocktail[], Error>(['cocktails', only_possible, max_hand_add, scale], () =>
    fetchCocktails(only_possible, max_hand_add, scale),
  );
};

export const prepareCocktail = async (
  cocktail: Cocktail,
  volume: number,
  alcohol_factor: number,
  teamName?: string,
): Promise<CocktailStatus> => {
  return axiosInstance
    .post<CocktailStatus>(`${cocktail_url}/prepare/${cocktail.id}`, {
      volume,
      alcohol_factor,
      selected_team: teamName,
    })
    .then((res) => res.data);
};

export const getCocktailStatus = async (): Promise<CocktailStatus> => {
  return axiosInstance
    .get<CocktailStatus>(`${cocktail_url}/prepare/status`)
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error fetching cocktail status:', error);
      return {
        progress: 0,
        error: undefined,
        status: 'UNDEFINED',
      };
    });
};

export const stopCocktail = async (): Promise<void> => {
  return axiosInstance
    .post<void>(`${cocktail_url}/prepare/stop`)
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error stopping cocktail preparation:', error);
    });
};

export const cancelPayment = async (): Promise<void> => {
  return axiosInstance
    .post<void>(`${cocktail_url}/prepare/payment/cancel`)
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error cancelling payment:', error);
    });
};

export const deleteCocktail = async (id: number): Promise<{ message: string }> => {
  return axiosInstance.delete<{ message: string }>(`${cocktail_url}/${id}`).then((res) => res.data);
};

export const postCocktail = async (cocktail: CocktailInput): Promise<Cocktail> => {
  return axiosInstance.post<Cocktail>(cocktail_url, cocktail).then((res) => res.data);
};

export const updateCocktail = async (cocktail: CocktailInput): Promise<Cocktail> => {
  return axiosInstance.put<Cocktail>(`${cocktail_url}/${cocktail.id}`, cocktail).then((res) => res.data);
};

export const uploadCocktailImage = async (id: number, file: File): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  return axiosInstance
    .post<{ message: string }>(`${cocktail_url}/${id}/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    .then((res) => res.data);
};

export const deleteCocktailImage = async (id: number): Promise<{ message: string }> => {
  return axiosInstance.delete<{ message: string }>(`${cocktail_url}/${id}/image`).then((res) => res.data);
};

export const enableAllRecipes = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${cocktail_url}/enable`).then((res) => res.data);
};

export const calculateOptimal = async (
  number_ingredients: number,
  algorithm: 'greedy' | 'local' | 'ilp' = 'ilp',
): Promise<{ cocktails: Cocktail[]; ingredients: Ingredient[] }> => {
  return axiosInstance
    .get<{ cocktails: Cocktail[]; ingredients: Ingredient[] }>(`${cocktail_url}/calculate`, {
      params: { number_ingredients, algorithm },
    })
    .then((res) => res.data);
};
