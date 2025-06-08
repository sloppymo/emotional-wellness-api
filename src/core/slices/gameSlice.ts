import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { RootState } from '../store'

export interface GameState {
  currentTurn: number
  maxTurns: number
  gamePhase: 'menu' | 'playing' | 'paused' | 'ended'
  isLoading: boolean
  currentPlayer: 'government' | 'insurgents'
  gameMode: 'campaign' | 'custom'
  difficulty: 'easy' | 'normal' | 'hard'
}

const initialState: GameState = {
  currentTurn: 1,
  maxTurns: 48, // 4 years * 12 months
  gamePhase: 'menu',
  isLoading: false,
  currentPlayer: 'government',
  gameMode: 'campaign',
  difficulty: 'normal',
}

const gameSlice = createSlice({
  name: 'game',
  initialState,
  reducers: {
    startGame: (state) => {
      state.gamePhase = 'playing'
      state.currentTurn = 1
      state.isLoading = false
    },
    
    pauseGame: (state) => {
      state.gamePhase = 'paused'
    },
    
    resumeGame: (state) => {
      state.gamePhase = 'playing'
    },
    
    endGame: (state) => {
      state.gamePhase = 'ended'
    },
    
    nextTurn: (state) => {
      if (state.currentTurn < state.maxTurns) {
        state.currentTurn += 1
        state.currentPlayer = state.currentPlayer === 'government' ? 'insurgents' : 'government'
      } else {
        state.gamePhase = 'ended'
      }
    },
    
    setGameMode: (state, action: PayloadAction<'campaign' | 'custom'>) => {
      state.gameMode = action.payload
    },
    
    setDifficulty: (state, action: PayloadAction<'easy' | 'normal' | 'hard'>) => {
      state.difficulty = action.payload
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    
    resetGame: (state) => {
      return initialState
    },
  },
})

export const {
  startGame,
  pauseGame,
  resumeGame,
  endGame,
  nextTurn,
  setGameMode,
  setDifficulty,
  setLoading,
  resetGame,
} = gameSlice.actions

// Selectors
export const selectGameState = (state: RootState) => state.game
export const selectCurrentTurn = (state: RootState) => state.game.currentTurn
export const selectGamePhase = (state: RootState) => state.game.gamePhase
export const selectCurrentPlayer = (state: RootState) => state.game.currentPlayer
export const selectIsLoading = (state: RootState) => state.game.isLoading

export default gameSlice.reducer 