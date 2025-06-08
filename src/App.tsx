import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'

import { GameScreen } from './ui/screens/GameScreen'
import { MainMenu } from './ui/screens/MainMenu'
import { LoadingScreen } from './ui/screens/LoadingScreen'
import { useAppSelector } from './core/hooks'
import { selectGameState } from './core/slices/gameSlice'

const App: React.FC = () => {
  const gameState = useAppSelector(selectGameState)

  return (
    <Box sx={{ height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Routes>
        <Route path="/" element={<MainMenu />} />
        <Route path="/game" element={<GameScreen />} />
        <Route path="/loading" element={<LoadingScreen />} />
      </Routes>
    </Box>
  )
}

export default App 