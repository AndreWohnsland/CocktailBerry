import { useEffect, useRef, useState } from 'react';
import { type UseQueryResult, useQuery } from 'react-query';
import type { CurrentWaiterState, Waiter, WaiterCreate, WaiterLogEntry, WaiterUpdate } from '../types/models';
import { API_URL, axiosInstance } from './common';

const waitersUrl = '/waiters';

const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 16_000;

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
  const [isConnected, setIsConnected] = useState(false);
  const prevStateRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setWaiter(null);
      setIsConnected(false);
      prevStateRef.current = null;
      return undefined;
    }

    let disposed = false;
    let reconnectAttempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let ws: WebSocket | null = null;

    const connect = () => {
      if (disposed) return;
      const wsUrl = `${API_URL.replace(/^http/, 'ws')}/waiters/ws/current`;
      ws = new WebSocket(wsUrl);
      let wasConnected = false;

      ws.onopen = () => {
        console.log('Waiter WebSocket connected');
        wasConnected = true;
        reconnectAttempt = 0;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: CurrentWaiterState = JSON.parse(event.data);
          // Use serialized string to detect any change (nfc_id, waiter)
          const stateKey = JSON.stringify(data);
          if (stateKey !== prevStateRef.current) {
            prevStateRef.current = stateKey;
            setWaiter(data);
          }
        } catch (error) {
          console.error('Error parsing waiter WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        if (wasConnected) {
          console.error('Waiter WebSocket error:', error);
        }
      };

      ws.onclose = () => {
        if (wasConnected) {
          console.log('Waiter WebSocket closed');
        }
        setIsConnected(false);
        // Schedule reconnection with exponential backoff
        if (!disposed) {
          const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempt, RECONNECT_MAX_DELAY_MS);
          reconnectAttempt += 1;
          console.log(`Waiter WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttempt})`);
          reconnectTimer = setTimeout(connect, delay);
        }
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      ws?.close();
    };
  }, [enabled]);

  return { waiter, isConnected };
};
