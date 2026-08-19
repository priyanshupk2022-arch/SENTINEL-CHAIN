import { useState, useEffect, useRef } from 'react';

export interface TelemetryFrame {
  event: string;
  data: any;
  timestamp: string;
}

export function useTelemetryStream(url: string = '/api/stream/telemetry') {
  const [frames, setFrames] = useState<TelemetryFrame[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'LIVE' | 'MOCK' | 'OFFLINE'>('OFFLINE');
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const backoffRef = useRef(1000); // Start with 1s

  useEffect(() => {
    function connect() {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnectionStatus(url.includes('mock') ? 'MOCK' : 'LIVE');
        backoffRef.current = 1000; // Reset backoff on successful connect
      };

      es.onmessage = (event) => {
        try {
          const frame: TelemetryFrame = JSON.parse(event.data);
          setFrames((prev) => [...prev.slice(-99), frame]); // Keep last 100 frames
        } catch (error) {
          console.error('Failed to parse telemetry frame', error);
        }
      };

      es.onerror = () => {
        setConnectionStatus('OFFLINE');
        es.close();
        
        // Exponential backoff
        const nextBackoff = Math.min(backoffRef.current * 2, 30000);
        backoffRef.current = nextBackoff;
        
        reconnectTimeoutRef.current = setTimeout(connect, nextBackoff);
      };
    }

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [url]);

  return { frames, connectionStatus };
}
