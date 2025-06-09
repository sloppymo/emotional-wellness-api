import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Paper, 
  Grid, 
  Box, 
  Card, 
  CardContent, 
  CardActions, 
  Button,
  Skeleton,
  Alert,
  Chip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { gameService, authService } from '../services/api';

interface Game {
  id: string;
  name: string;
  turn: number;
  start_date: string;
  player_faction: {
    name: string;
    type: string;
    ideology: string;
  };
  scenario: {
    name: string;
    description: string;
  };
  state: string;
}

interface User {
  id: string;
  username: string;
  email: string;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get current user
        const userData = await authService.getCurrentUser();
        setUser(userData);
        
        // Get user's games
        const gamesData = await gameService.getGames();
        setGames(gamesData);
        
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard data');
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  const handleCreateGame = () => {
    navigate('/games/new');
  };

  const handleContinueGame = (gameId: string) => {
    navigate(`/games/${gameId}`);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleCreateGame}
        >
          Create New Game
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* User info card */}
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Your Profile
            </Typography>
            
            {loading ? (
              <>
                <Skeleton height={30} width="60%" />
                <Skeleton height={20} width="80%" />
                <Skeleton height={20} width="40%" />
              </>
            ) : (
              <>
                <Typography variant="body1">
                  <strong>Username:</strong> {user?.username}
                </Typography>
                <Typography variant="body1">
                  <strong>Email:</strong> {user?.email}
                </Typography>
                <Box mt={2}>
                  <Typography variant="body2" color="text.secondary">
                    Total games: {games.length}
                  </Typography>
                </Box>
              </>
            )}
          </Paper>
        </Grid>

        {/* Recent games */}
        <Grid item xs={12} md={8}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              Recent Games
            </Typography>
            
            {loading ? (
              <>
                <Skeleton height={100} />
                <Skeleton height={100} />
              </>
            ) : games.length === 0 ? (
              <Box py={2}>
                <Typography color="text.secondary">
                  You haven't created any games yet. Click "Create New Game" to get started.
                </Typography>
              </Box>
            ) : (
              <Grid container spacing={2}>
                {games.slice(0, 3).map(game => (
                  <Grid item xs={12} key={game.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="h6" component="h3">
                            {game.name}
                          </Typography>
                          <Chip 
                            label={`Turn ${game.turn}`} 
                            color="primary" 
                            size="small" 
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {game.scenario.name}
                        </Typography>
                        <Typography variant="body2">
                          Playing as: <strong>{game.player_faction.name}</strong> ({game.player_faction.type})
                        </Typography>
                      </CardContent>
                      <CardActions>
                        <Button 
                          size="small" 
                          color="primary"
                          onClick={() => handleContinueGame(game.id)}
                        >
                          Continue Game
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
                
                {games.length > 3 && (
                  <Grid item xs={12}>
                    <Button 
                      color="primary" 
                      onClick={() => navigate('/games')}
                      sx={{ mt: 1 }}
                    >
                      View All Games ({games.length})
                    </Button>
                  </Grid>
                )}
              </Grid>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
