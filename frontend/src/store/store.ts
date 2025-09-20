import { configureStore } from '@reduxjs/toolkit';

// TODO: Import slices as they are created
// import authSlice from './authSlice';
// import inventorySlice from './inventorySlice';

export const store = configureStore({
  reducer: {
    // auth: authSlice,
    // inventory: inventorySlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;