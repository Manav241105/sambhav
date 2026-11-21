import { useContext } from 'react';
import { WebSocketContext } from './webSocketContextObject';

/** { connected, subscribe(type, callback) => unsubscribe } for the dashboard event stream. */
export function useWebSocketContext() {
    return useContext(WebSocketContext);
}
