import { useQuery, type UseQueryResult } from 'react-query';
import type { Ingredient, IngredientInput } from '../types/models';
import { axiosInstance } from './common';

const ingredient_url = '/ingredients';

export const fetchIngredients = async (hand: boolean = true, machine: boolean = true): Promise<Ingredient[]> => {
  return axiosInstance
    .get<Ingredient[]>(ingredient_url, {
      params: {
        hand,
        machine,
      },
    })
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error fetching Ingredient:', error);
      return [];
    });
};

export const useIngredients = (hand: boolean = true, machine: boolean = true): UseQueryResult<Ingredient[], Error> => {
  return useQuery<Ingredient[], Error>(['ingredients', hand, machine], () => fetchIngredients(hand, machine));
};

export const useAvailableIngredients = (): UseQueryResult<number[], Error> => {
  return useQuery<number[], Error>(['availableIngredients'], () =>
    axiosInstance
      .get<number[]>(`${ingredient_url}/available`)
      .then((res) => res.data)
      .catch((error) => {
        console.error('Error fetching Ingredient:', error);
        return [];
      }),
  );
};

export const postAvailableIngredients = async (available: number[]): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${ingredient_url}/available`, available).then((res) => res.data);
};

export const deleteIngredient = async (id: number): Promise<{ message: string }> => {
  return axiosInstance.delete<{ message: string }>(`${ingredient_url}/${id}`).then((res) => res.data);
};

export const postIngredient = async (ingredient: IngredientInput): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(ingredient_url, ingredient).then((res) => res.data);
};

export const updateIngredient = async (ingredient: IngredientInput): Promise<{ message: string }> => {
  return axiosInstance
    .put<{ message: string }>(`${ingredient_url}/${ingredient.id}`, ingredient)
    .then((res) => res.data);
};

export const prepareIngredient = async (ingredient_id: number, amount: number): Promise<{ status: string }> => {
  return axiosInstance
    .post<{ status: string }>(`${ingredient_url}/${ingredient_id}/prepare`, null, { params: { amount } })
    .then((res) => res.data);
};
