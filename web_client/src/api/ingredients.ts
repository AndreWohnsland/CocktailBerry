import { useQuery, UseQueryResult } from 'react-query';

import axios from 'axios';
import { Ingredient } from '../types/models';
import { API_URL } from './common';

const ingredient_url = `${API_URL}/ingredients`;

export const fetchIngredients = async (hand: boolean = true, machine: boolean = true): Promise<Ingredient[]> => {
  const params = new URLSearchParams({ hand: hand.toString(), machine: machine.toString() });

  return axios
    .get<Ingredient[]>(`${ingredient_url}?${params.toString()}`, {
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
  return useQuery<Ingredient[], Error>(['cocktails', hand, machine], () => fetchIngredients(hand, machine));
};
