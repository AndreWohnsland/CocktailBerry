import { useEffect, useRef, useState } from 'react';
import { API_URL } from './common';

const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 16_000;

interface ReconnectingWebSocketOptions<T> {
  enabled: boolean;
  path: string;
  label: string;
  onMessage: (data: T) => void;
  onReset?: () => void;
}

export const useReconnectingWebSocket = <T>({
  enabled,
  path,
  label,
  onMessage,
  onReset,
}: ReconnectingWebSocketOptions<T>) => {
  const [isConnected, setIsConnected] = useState(false);

  // Stable refs so effect doesn't restart when callbacks change identity
  const onMessageRef = useRef(onMessage);
  const onResetRef = useRef(onReset);
  onMessageRef.current = onMessage;
  onResetRef.current = onReset;

  useEffect(() => {
    if (!enabled) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setIsConnected(false);
      onResetRef.current?.();
      return undefined;
    }

    let disposed = false;
    let reconnectAttempt = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let ws: WebSocket | null = null;

    const connect = () => {
      if (disposed) return;
      const wsUrl = `${API_URL.replace(/^http/, 'ws')}${path}`;
      ws = new WebSocket(wsUrl);
      let wasConnected = false;

      ws.onopen = () => {
        console.log(`${label} WebSocket connected`);
        wasConnected = true;
        reconnectAttempt = 0;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: T = JSON.parse(event.data);
          onMessageRef.current(data);
        } catch (error) {
          console.error(`Error parsing ${label} WebSocket message:`, error);
        }
      };

      ws.onerror = (error) => {
        if (wasConnected) {
          console.error(`${label} WebSocket error:`, error);
        }
      };

      ws.onclose = () => {
        if (wasConnected) {
          console.log(`${label} WebSocket closed`);
        }
        setIsConnected(false);
        if (!disposed) {
          const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** reconnectAttempt, RECONNECT_MAX_DELAY_MS);
          reconnectAttempt += 1;
          console.log(`${label} WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttempt})`);
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
  }, [enabled, path, label]);

  return { isConnected };
};
