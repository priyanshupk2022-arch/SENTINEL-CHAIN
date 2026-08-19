import { useState, useEffect, useCallback } from 'react';

export interface TelemetryFrame {
  id?: number;
  node_id: string;
  status: string;
  message: string;
  payload?: any;
  timestamp?: string;
}

export function useTelemetryStream() {
  const [frames, setFrames] = useState<TelemetryFrame[]>([]);
  const [latestFrame, setLatestFrame] = useState<TelemetryFrame | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'LIVE' | 'OFFLINE' | 'CONNECTING'>('CONNECTING');
  const [activeNodes, setActiveNodes] = useState<Record<string, string>>({});

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let reconnectTimeout: any = null;

    const connectSSE = () => {
      try {
        const url = process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/telemetry/stream` 
          : 'http://localhost:8000/api/telemetry/stream';

        eventSource = new EventSource(url);

        eventSource.onopen = () => {
          setConnectionStatus('LIVE');
        };

        eventSource.onmessage = (event) => {
          try {
            if (event.data.startsWith('{')) {
              const data: TelemetryFrame = JSON.parse(event.data);
              setLatestFrame(data);
              setFrames((prev) => [data, ...prev.slice(0, 100)]);

              if (data.node_id) {
                setActiveNodes((prev) => ({
                  ...prev,
                  [data.node_id]: data.status
                }));
              }
            }
          } catch (err) {
            console.error('Error parsing SSE event:', err);
          }
        };

        eventSource.onerror = () => {
          setConnectionStatus('OFFLINE');
          eventSource?.close();
          reconnectTimeout = setTimeout(connectSSE, 3000);
        };
      } catch (err) {
        setConnectionStatus('OFFLINE');
        reconnectTimeout = setTimeout(connectSSE, 3000);
      }
    };

    connectSSE();

    return () => {
      if (eventSource) eventSource.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  return {
    frames,
    latestFrame,
    connectionStatus,
    activeNodes
  };
}
