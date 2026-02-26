import { useWebSocketContext } from '../contexts/WebSocketContext';

/**
 * useWebSocket — backwards-compatible wrapper around the new WebSocketProvider.
 * Returns { lastEvent, connected } — same API as before.
 *
 * The actual WebSocket connection is managed by <WebSocketProvider> in App.jsx.
 * This hook simply reads from context, so multiple calls share one connection.
 */
export default function useWebSocket() {
    const { lastEvent, connected } = useWebSocketContext();
    return { lastEvent, connected };
}
