import { Bottle } from '../types/models';
import { useQuery, UseQueryResult } from 'react-query';
import { API_URL, axiosInstance } from './common';

const bottle_url = `${API_URL}/bottles`;

export const getBottles = async (): Promise<Bottle[]> => {
  return axiosInstance.get<Bottle[]>(`${bottle_url}`).then((response) => response.data);
};

export const useBottles = (): UseQueryResult<Bottle[], Error> => {
  return useQuery<Bottle[], Error>('bottles', getBottles);
};

export const refillBottle = async (bottleNumbers: number[]) => {
  return axiosInstance.post(`${bottle_url}/refill`, bottleNumbers).then((response) => response.data);
};

export const updateBottle = async (bottleId: number, ingredientId: number, amount?: number) => {
  return axiosInstance
    .put(`${bottle_url}/${bottleId}`, null, { params: { ingredient_id: ingredientId, amount } })
    .then((response) => response.data);
};
