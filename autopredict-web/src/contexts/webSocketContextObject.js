import { createContext } from 'react';

// The context object lives in its own module so the provider file only exports components.
export const WebSocketContext = createContext({
    connected: false,
    subscribe: () => () => {},
});
