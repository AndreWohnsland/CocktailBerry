import { useQuery, UseQueryResult } from 'react-query';
import axios from 'axios';
import { Ingredient, IngredientInput } from '../types/models';
import { API_URL } from './common';

const ingredient_url = `${API_URL}/ingredients`;

export const fetchIngredients = async (hand: boolean = true, machine: boolean = true): Promise<Ingredient[]> => {
  return axios
    .get<Ingredient[]>(ingredient_url, {
      params: {
        hand,
        machine,
      },
      headers: {
        Accept: 'application/json',
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
    axios
      .get<number[]>(`${ingredient_url}/available`, {
        headers: {
          Accept: 'application/json',
        },
      })
      .then((res) => res.data)
      .catch((error) => {
        console.error('Error fetching Ingredient:', error);
        return [];
      }),
  );
};

export const postAvailableIngredients = async (available: number[]): Promise<{ message: string }> => {
  return axios
    .post<{ message: string }>(`${ingredient_url}/available`, available, {
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    })
    .then((res) => res.data);
};

export const deleteIngredient = async (id: number): Promise<{ message: string }> => {
  return axios
    .delete<{ message: string }>(`${ingredient_url}/${id}`, {
      headers: {
        Accept: 'application/json',
      },
    })
    .then((res) => res.data);
};

export const postIngredient = async (ingredient: IngredientInput): Promise<{ message: string }> => {
  return axios
    .post<{ message: string }>(ingredient_url, ingredient, {
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    })
    .then((res) => res.data);
};

export const updateIngredient = async (ingredient: IngredientInput): Promise<{ message: string }> => {
  return axios
    .put<{ message: string }>(`${ingredient_url}/${ingredient.id}`, ingredient, {
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    })
    .then((res) => res.data);
};
