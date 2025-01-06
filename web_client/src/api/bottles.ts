import { Bottle } from '../types/models';
import { useQuery, UseQueryResult } from 'react-query';
import { axiosInstance } from './common';

const bottle_url = '/bottles';

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

export const calibrateBottle = async (bottle_id: number, amount: number): Promise<{ message: string }> => {
  return axiosInstance
    .post<{ message: string }>(`${bottle_url}/${bottle_id}/calibrate`, null, { params: { amount } })
    .then((response) => response.data);
};
