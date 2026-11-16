import { useCallback, useEffect, useRef, useState } from 'react';
import { OneEuroKeypointFilter } from '../engine/OneEuroFilter';
import type {
  ExerciseMode,
  NormalizedKeypoint,
  PersonTelemetry,
  TelemetryPacket,
  WebSocketServerMessage,
} from '../engine/types';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

interface UsePoseWebSocketResult {
  status: ConnectionStatus;
  activeMode: ExerciseMode;
  persons: PersonTelemetry[];
  fps: number;
  rttMs: number;
  inferMs: number;
  canSendFrame: () => boolean;
  sendFrame: (jpegBuffer: ArrayBuffer) => boolean;
  setMode: (mode: ExerciseMode) => void;
  resetReps: () => void;
}

const IN_FLIGHT_STALE_MS = 1500;

export function usePoseWebSocket(wsUrl: string): UsePoseWebSocketResult {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [activeMode, setActiveMode] = useState<ExerciseMode>('PUSH-UP');
  const [persons, setPersons] = useState<PersonTelemetry[]>([]);
  const [fps, setFps] = useState<number>(0);
  const [rttMs, setRttMs] = useState<number>(0);
  const [inferMs, setInferMs] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const inFlightRef = useRef<boolean>(false);
  const lastSendTsRef = useRef<number>(0);
  const filtersRef = useRef<Map<number, OneEuroKeypointFilter>>(new Map());

  const smoothPersons = useCallback((rawPersons: PersonTelemetry[]): PersonTelemetry[] => {
    const now = Date.now();
    const activeIds = new Set<number>();

    const smoothed = rawPersons.map(person => {
      activeIds.add(person.track_id);
      let filter = filtersRef.current.get(person.track_id);
      if (!filter) {
        filter = new OneEuroKeypointFilter(1.2, 0.02);
        filtersRef.current.set(person.track_id, filter);
      }

      const flat: number[] = [];
      for (const kp of person.keypoints) {
        flat.push(kp[0], kp[1]);
      }
      const filtered = filter.filterFlat(flat, now);
      const nextKpts: NormalizedKeypoint[] = person.keypoints.map((kp, i) => [
        kp[2] >= 0.35 ? filtered[i * 2] : kp[0],
        kp[2] >= 0.35 ? filtered[i * 2 + 1] : kp[1],
        kp[2],
      ]);

      return { ...person, keypoints: nextKpts };
    });

    for (const tid of filtersRef.current.keys()) {
      if (!activeIds.has(tid)) {
        filtersRef.current.delete(tid);
      }
    }
    return smoothed;
  }, []);

  useEffect(() => {
    let closedByUser = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (closedByUser || !wsUrl.trim()) {
        return;
      }

      setStatus('connecting');
      inFlightRef.current = false;

      const ws = new WebSocket(wsUrl.trim());
      wsRef.current = ws;

      ws.onopen = () => {
        if (!closedByUser) {
          setStatus('connected');
        }
      };

      ws.onmessage = event => {
        if (typeof event.data !== 'string') {
          return;
        }
        try {
          const msg = JSON.parse(event.data) as WebSocketServerMessage;
          if (msg.type === 'connected' || msg.type === 'mode_updated') {
            setActiveMode(msg.active_mode);
          } else if (msg.type === 'telemetry') {
            const packet = msg as TelemetryPacket;
            inFlightRef.current = false;
            const now = Date.now();
            if (lastSendTsRef.current > 0) {
              setRttMs(Math.max(0, now - lastSendTsRef.current));
            }
            if (typeof packet.infer_ms === 'number') {
              setInferMs(Math.round(packet.infer_ms));
            }
            setFps(packet.fps ?? 0);
            setActiveMode(packet.active_mode);
            setPersons(smoothPersons(packet.persons ?? []));
          } else if (msg.type === 'reset_done') {
            setPersons([]);
          }
        } catch {
          inFlightRef.current = false;
        }
      };

      ws.onerror = () => {
        inFlightRef.current = false;
      };

      ws.onclose = () => {
        inFlightRef.current = false;
        if (!closedByUser) {
          setStatus('disconnected');
          reconnectTimer = setTimeout(connect, 1800);
        }
      };
    };

    connect();

    return () => {
      closedByUser = true;
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [wsUrl, smoothPersons]);

  const canSendFrame = useCallback((): boolean => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return false;
    }
    if (inFlightRef.current && Date.now() - lastSendTsRef.current < IN_FLIGHT_STALE_MS) {
      return false;
    }
    return true;
  }, []);

  const sendFrame = useCallback(
    (jpegBuffer: ArrayBuffer): boolean => {
      if (!canSendFrame()) {
        return false;
      }
      const ws = wsRef.current;
      if (!ws) {
        return false;
      }
      inFlightRef.current = true;
      lastSendTsRef.current = Date.now();
      ws.send(jpegBuffer);
      return true;
    },
    [canSendFrame],
  );

  const setMode = useCallback((mode: ExerciseMode) => {
    setActiveMode(mode);
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'set_mode', mode }));
    }
  }, []);

  const resetReps = useCallback(() => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'reset' }));
    }
  }, []);

  return {
    status,
    activeMode,
    persons,
    fps,
    rttMs,
    inferMs,
    canSendFrame,
    sendFrame,
    setMode,
    resetReps,
  };
}
