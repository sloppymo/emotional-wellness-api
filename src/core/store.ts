import { configureStore } from '@reduxjs/toolkit'
import gameSlice from './slices/gameSlice'
import factionSlice from './slices/factionSlice'
import uiSlice from './slices/uiSlice'
import heatSlice from './slices/heatSlice'
import sylvaSlice from './slices/sylvaSlice'

export const store = configureStore({
  reducer: {
    game: gameSlice,
    factions: factionSlice,
    ui: uiSlice,
    heat: heatSlice,
    sylva: sylvaSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch 