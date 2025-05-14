import { configureStore } from '@reduxjs/toolkit';
import kgVisualizationReducer from '../features/kgVisualization/kgVisualizationSlice';

export const store = configureStore({
    reducer: {
        kgVisualization: kgVisualizationReducer,
        // Add other reducers here as your application grows
    },
    // Middleware can be added here, e.g., for logging or other side effects
    // getDefaultMiddleware returns an array of middleware included by default with Redux Toolkit
    // middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(loggerMiddleware),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
// Inferred type: {kgVisualization: KGVisualizationState, ...}
export type AppDispatch = typeof store.dispatch; 