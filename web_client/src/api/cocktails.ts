import { useQuery, UseQueryResult } from 'react-query';
import axios from 'axios';
import { Cocktail, CocktailStatus } from '../types/models';
import { API_URL } from './common';

const cocktail_url = `${API_URL}/cocktails`;

export const fetchCocktails = async (): Promise<Cocktail[]> => {
  return axios
    .get<Cocktail[]>(cocktail_url, {
      headers: {
        Accept: 'application/json',
      },
    })
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error fetching cocktails:', error);
      return [];
    });
};

export const useCocktails = (): UseQueryResult<Cocktail[], Error> => {
  return useQuery<Cocktail[], Error>('cocktails', fetchCocktails);
};

export const prepareCocktail = async (
  cocktail: Cocktail,
  volume: number,
  alcohol_factor: number,
  is_virgin: boolean,
): Promise<CocktailStatus> => {
  return axios
    .post<CocktailStatus>(
      `${cocktail_url}/prepare/${cocktail.id}`,
      {
        volume,
        alcohol_factor,
        is_virgin,
      },
      {
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      },
    )
    .then((res) => res.data);
};

export const getCocktailStatus = async (): Promise<CocktailStatus> => {
  return axios
    .get<CocktailStatus>(`${cocktail_url}/prepare/status`, {
      headers: {
        Accept: 'application/json',
      },
    })
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error fetching cocktail status:', error);
      return {
        progress: 0,
        completed: false,
        error: undefined,
        status: 'UNDEFINED',
      };
    });
};

export const stopCocktail = async (): Promise<void> => {
  return axios
    .post<void>(
      `${cocktail_url}/prepare/stop`,
      {},
      {
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        },
      },
    )
    .then((res) => res.data)
    .catch((error) => {
      console.error('Error stopping cocktail preparation:', error);
    });
};
