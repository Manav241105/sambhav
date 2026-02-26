import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

/**
 * useWebSocketData — subscribes to a **specific** WebSocket event type
 * so only components interested in that type re-render.
 *
 * Usage:
 *   const { latestEvent, eventCount } = useWebSocketData('DIAGNOSIS_UPDATED');
 *
 *   useEffect(() => {
 *     if (latestEvent) refreshVehicleCard(latestEvent.payload.vehicle_id);
 *   }, [latestEvent]);
 *
 * Pass '*' (wildcard) to receive every event.
 *
 * @param {string} eventType — one of:
 *   VEHICLE_UPDATED | BOOKING_CREATED | BOOKING_CANCELLED |
 *   ALERT_FIRED | CONVERSATION_TURN | DIAGNOSIS_UPDATED |
 *   WORKFLOW_COMPLETED | '*'
 * @returns {{ latestEvent: object|null, eventCount: number, connected: boolean }}
 */
export default function useWebSocketData(eventType) {
    const { subscribe, connected } = useWebSocketContext();
    const [latestEvent, setLatestEvent] = useState(null);
    const countRef = useRef(0);
    const [eventCount, setEventCount] = useState(0);

    const handler = useCallback((event) => {
        setLatestEvent(event);
        countRef.current += 1;
        setEventCount(countRef.current);
    }, []);

    useEffect(() => {
        const unsub = subscribe(eventType, handler);
        return unsub;
    }, [eventType, subscribe, handler]);

    return { latestEvent, eventCount, connected };
}
