import { configureStore } from '@reduxjs/toolkit';
import chatReducer from './slices/chatSlice';
import systemReducer from './slices/systemSlice';
import agentReducer from './slices/agentSlice';

export const store = configureStore({
  reducer: {
    chat: chatReducer,
    system: systemReducer,
    agent: agentReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export type tState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 