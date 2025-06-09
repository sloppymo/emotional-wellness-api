import React, { useEffect, useState } from 'react';
import { 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  CardActions, 
  Button, 
  Grid,
  Skeleton,
  Alert,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Divider
} from '@mui/material';
import { Search as SearchIcon, Add as AddIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { gameService } from '../services/api';

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
  last_updated: string;
}

const GameList: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [games, setGames] = useState<Game[]>([]);
  const [filteredGames, setFilteredGames] = useState<Game[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const gamesData = await gameService.getGames();
        setGames(gamesData);
        setFilteredGames(gamesData);
        
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load games');
        setLoading(false);
      }
    };
    
    fetchGames();
  }, []);

  useEffect(() => {
    // Filter games based on search term
    if (searchTerm) {
      const filtered = games.filter(game => 
        game.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.scenario.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        game.player_faction.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredGames(filtered);
    } else {
      setFilteredGames(games);
    }
  }, [searchTerm, games]);

  const handleCreateGame = () => {
    navigate('/games/new');
  };

  const handleGameClick = (gameId: string) => {
    navigate(`/games/${gameId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" component="h1">
          Your Games
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleCreateGame}
          startIcon={<AddIcon />}
        >
          Create New Game
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box mb={3}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search games..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <IconButton edge="start">
                  <SearchIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {loading ? (
        <Grid container spacing={3}>
          {[1, 2, 3].map(i => (
            <Grid item xs={12} md={6} lg={4} key={i}>
              <Card>
                <CardContent>
                  <Skeleton height={28} width="60%" />
                  <Skeleton height={20} width="40%" />
                  <Skeleton height={20} width="80%" />
                  <Skeleton height={20} width="30%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : filteredGames.length === 0 ? (
        <Box textAlign="center" py={5}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No games found
          </Typography>
          <Typography color="text.secondary">
            {searchTerm ? "Try a different search term or" : "You haven't created any games yet."} 
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            sx={{ mt: 2 }}
            onClick={handleCreateGame}
            startIcon={<AddIcon />}
          >
            Create New Game
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredGames.map(game => (
            <Grid item xs={12} md={6} lg={4} key={game.id}>
              <Card sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                  cursor: 'pointer'
                } 
              }} onClick={() => handleGameClick(game.id)}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="h6" component="h3" noWrap>
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
                  
                  <Divider sx={{ my: 1 }} />
                  
                  <Typography variant="body2">
                    <strong>Faction:</strong> {game.player_faction.name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Ideology:</strong> {game.player_faction.ideology}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Started:</strong> {formatDate(game.start_date)}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Last played:</strong> {formatDate(game.last_updated || game.start_date)}
                  </Typography>
                  
                  <Box mt={1}>
                    <Chip 
                      label={game.state === 'active' ? 'Active' : 'Completed'}
                      color={game.state === 'active' ? 'success' : 'default'}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button size="small" color="primary">
                    Continue Game
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default GameList;
