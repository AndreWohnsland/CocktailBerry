import { useRef, useState } from 'react';
import { type UseQueryResult, useQuery } from 'react-query';
import type { CurrentWaiterState, Waiter, WaiterCreate, WaiterLogEntry, WaiterUpdate } from '../types/models';
import { axiosInstance } from './common';
import { useReconnectingWebSocket } from './useReconnectingWebSocket';

const waitersUrl = '/waiters';

// Logout

export const logoutWaiter = async (): Promise<{ message: string }> => {
  return axiosInstance.post<{ message: string }>(`${waitersUrl}/logout`).then((res) => res.data);
};

// CRUD operations

export const getWaiters = async (): Promise<Waiter[]> => {
  return axiosInstance.get<Waiter[]>(waitersUrl).then((res) => res.data);
};

export const useWaiters = (): UseQueryResult<Waiter[], Error> => {
  return useQuery<Waiter[], Error>('waiters', getWaiters);
};

export const createWaiter = async (data: WaiterCreate): Promise<Waiter> => {
  return axiosInstance.post<Waiter>(waitersUrl, data).then((res) => res.data);
};

export const updateWaiter = async (nfcId: string, data: WaiterUpdate): Promise<Waiter> => {
  return axiosInstance.put<Waiter>(`${waitersUrl}/${nfcId}`, data).then((res) => res.data);
};

export const deleteWaiter = async (nfcId: string): Promise<{ message: string }> => {
  return axiosInstance.delete<{ message: string }>(`${waitersUrl}/${nfcId}`).then((res) => res.data);
};

// Logs

export const getWaiterLogs = async (): Promise<WaiterLogEntry[]> => {
  return axiosInstance.get<WaiterLogEntry[]>(`${waitersUrl}/logs`).then((res) => res.data);
};

export const useWaiterLogs = (): UseQueryResult<WaiterLogEntry[], Error> => {
  return useQuery<WaiterLogEntry[], Error>('waiterLogs', getWaiterLogs);
};

// Current waiter state

export const getCurrentWaiter = async (): Promise<Waiter | null> => {
  return axiosInstance.get<Waiter | null>(`${waitersUrl}/current`).then((res) => res.data);
};

export const useCurrentWaiter = (enabled: boolean): UseQueryResult<Waiter | null, Error> => {
  return useQuery<Waiter | null, Error>('currentWaiter', getCurrentWaiter, {
    enabled,
    staleTime: 5_000,
    refetchOnWindowFocus: true,
  });
};

// WebSocket for real-time waiter state

export const useWaiterWebSocket = (enabled: boolean) => {
  const [waiter, setWaiter] = useState<CurrentWaiterState | null>(null);
  const prevStateRef = useRef<string | null>(null);

  const { isConnected } = useReconnectingWebSocket<CurrentWaiterState>({
    enabled,
    path: '/waiters/ws/current',
    label: 'Waiter',
    onMessage: (data) => {
      const stateKey = JSON.stringify(data);
      if (stateKey !== prevStateRef.current) {
        prevStateRef.current = stateKey;
        setWaiter(data);
      }
    },
    onReset: () => {
      setWaiter(null);
      prevStateRef.current = null;
    },
  });

  return { waiter, isConnected };
};
