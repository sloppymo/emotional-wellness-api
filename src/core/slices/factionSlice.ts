import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import type { RootState } from '../store'

export interface FactionState {
  government: {
    resources: number
    support: number
    legitimacy: number
    capabilities: {
      military: number
      political: number
      economic: number
    }
  }
  insurgents: {
    resources: number
    support: number
    commitment: number
    capabilities: {
      guerrilla: number
      terror: number
      propaganda: number
    }
  }
}

const initialState: FactionState = {
  government: {
    resources: 100,
    support: 50,
    legitimacy: 70,
    capabilities: {
      military: 60,
      political: 50,
      economic: 40,
    },
  },
  insurgents: {
    resources: 30,
    support: 30,
    commitment: 80,
    capabilities: {
      guerrilla: 40,
      terror: 20,
      propaganda: 30,
    },
  },
}

const factionSlice = createSlice({
  name: 'factions',
  initialState,
  reducers: {
    updateGovernmentResources: (state, action: PayloadAction<number>) => {
      state.government.resources = Math.max(0, Math.min(100, state.government.resources + action.payload))
    },
    
    updateGovernmentSupport: (state, action: PayloadAction<number>) => {
      state.government.support = Math.max(0, Math.min(100, state.government.support + action.payload))
    },
    
    updateGovernmentLegitimacy: (state, action: PayloadAction<number>) => {
      state.government.legitimacy = Math.max(0, Math.min(100, state.government.legitimacy + action.payload))
    },
    
    updateInsurgentResources: (state, action: PayloadAction<number>) => {
      state.insurgents.resources = Math.max(0, Math.min(100, state.insurgents.resources + action.payload))
    },
    
    updateInsurgentSupport: (state, action: PayloadAction<number>) => {
      state.insurgents.support = Math.max(0, Math.min(100, state.insurgents.support + action.payload))
    },
    
    updateInsurgentCommitment: (state, action: PayloadAction<number>) => {
      state.insurgents.commitment = Math.max(0, Math.min(100, state.insurgents.commitment + action.payload))
    },
    
    updateGovernmentCapability: (state, action: PayloadAction<{type: 'military' | 'political' | 'economic', value: number}>) => {
      const { type, value } = action.payload
      state.government.capabilities[type] = Math.max(0, Math.min(100, state.government.capabilities[type] + value))
    },
    
    updateInsurgentCapability: (state, action: PayloadAction<{type: 'guerrilla' | 'terror' | 'propaganda', value: number}>) => {
      const { type, value } = action.payload
      state.insurgents.capabilities[type] = Math.max(0, Math.min(100, state.insurgents.capabilities[type] + value))
    },
    
    resetFactions: (state) => {
      return initialState
    },
  },
})

export const {
  updateGovernmentResources,
  updateGovernmentSupport,
  updateGovernmentLegitimacy,
  updateInsurgentResources,
  updateInsurgentSupport,
  updateInsurgentCommitment,
  updateGovernmentCapability,
  updateInsurgentCapability,
  resetFactions,
} = factionSlice.actions

// Selectors
export const selectFactions = (state: RootState) => state.factions
export const selectGovernment = (state: RootState) => state.factions.government
export const selectInsurgents = (state: RootState) => state.factions.insurgents

export default factionSlice.reducer 