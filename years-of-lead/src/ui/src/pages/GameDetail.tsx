import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  Chip, 
  Tabs, 
  Tab, 
  Divider, 
  List, 
  ListItem, 
  ListItemText,
  ListItemIcon,
  Avatar,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import {
  Public as PublicIcon,
  Group as GroupIcon,
  Person as PersonIcon,
  EventNote as EventNoteIcon,
  ArrowForward as ArrowForwardIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService, factionService, playerService } from '../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`game-tabpanel-${index}`}
      aria-labelledby={`game-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const GameDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [game, setGame] = useState<any>(null);
  const [factions, setFactions] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [characters, setCharacters] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [advancingTurn, setAdvancingTurn] = useState(false);
  const [confirmAdvanceTurn, setConfirmAdvanceTurn] = useState(false);

  useEffect(() => {
    if (!id) return;
    
    const fetchGameData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get game details
        const gameData = await gameService.getGameById(id);
        setGame(gameData);
        
        // Get factions in this game
        const factionsData = await factionService.getFactionByGame(id);
        setFactions(factionsData);
        
        // Get player characters
        const charactersData = await playerService.getPlayerCharacters(id);
        setCharacters(charactersData);
        
        // Get game events
        const eventsData = await gameService.getGameEvents(id);
        setEvents(eventsData);
        
        setLoading(false);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load game data');
        setLoading(false);
      }
    };
    
    fetchGameData();
  }, [id]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAdvanceTurn = async () => {
    if (!id) return;
    
    try {
      setAdvancingTurn(true);
      await gameService.advanceTurn(id);
      
      // Refresh game data
      const gameData = await gameService.getGameById(id);
      setGame(gameData);
      
      // Refresh events
      const eventsData = await gameService.getGameEvents(id);
      setEvents(eventsData);
      
      setConfirmAdvanceTurn(false);
      setAdvancingTurn(false);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to advance turn');
      setAdvancingTurn(false);
      setConfirmAdvanceTurn(false);
    }
  };

  const handleCharacterClick = (characterId: string) => {
    if (!id) return;
    navigate(`/games/${id}/characters/${characterId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box my={3}>
        <Alert severity="error">
          {error}
          <Button 
            color="inherit" 
            size="small" 
            onClick={() => navigate('/games')}
            sx={{ ml: 2 }}
          >
            Return to Games
          </Button>
        </Alert>
      </Box>
    );
  }

  if (!game) {
    return (
      <Box my={3}>
        <Alert severity="warning">
          Game not found
          <Button 
            color="inherit" 
            size="small" 
            onClick={() => navigate('/games')}
            sx={{ ml: 2 }}
          >
            Return to Games
          </Button>
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {game.name}
            </Typography>
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              {game.scenario.name}
            </Typography>
            <Box display="flex" alignItems="center" mt={1}>
              <Chip 
                label={`Turn ${game.turn}`} 
                color="primary" 
                sx={{ mr: 1 }} 
              />
              <Chip 
                label={game.state === 'active' ? 'Active' : 'Completed'} 
                color={game.state === 'active' ? 'success' : 'default'} 
              />
            </Box>
          </Box>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<ArrowForwardIcon />}
            disabled={advancingTurn || game.state !== 'active'}
            onClick={() => setConfirmAdvanceTurn(true)}
          >
            {advancingTurn ? 'Processing...' : 'Advance Turn'}
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="body2">
              <strong>Started:</strong> {formatDate(game.start_date)}
            </Typography>
            <Typography variant="body2">
              <strong>Last updated:</strong> {formatDate(game.last_updated || game.start_date)}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2">
              <strong>Your Faction:</strong> {game.player_faction.name}
            </Typography>
            <Typography variant="body2">
              <strong>Ideology:</strong> {game.player_faction.ideology}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
      
      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="game tabs">
            <Tab icon={<PublicIcon />} iconPosition="start" label="Overview" />
            <Tab icon={<GroupIcon />} iconPosition="start" label="Factions" />
            <Tab icon={<PersonIcon />} iconPosition="start" label="Characters" />
            <Tab icon={<EventNoteIcon />} iconPosition="start" label="Events" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Scenario Description
                </Typography>
                <Typography variant="body1">
                  {game.scenario.description || "No description available."}
                </Typography>
              </Paper>
              
              <Paper elevation={1} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Events
                </Typography>
                {events.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No events have occurred yet.
                  </Typography>
                ) : (
                  <List>
                    {events.slice(0, 5).map((event, index) => (
                      <ListItem key={index} divider={index < 4}>
                        <ListItemIcon>
                          <NotificationsIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={event.title} 
                          secondary={`Turn ${event.turn} - ${formatDate(event.date)}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
                {events.length > 5 && (
                  <Box mt={2} textAlign="center">
                    <Button 
                      color="primary" 
                      onClick={() => setTabValue(3)}
                    >
                      View All Events
                    </Button>
                  </Box>
                )}
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Faction Status
                </Typography>
                <Box display="flex" alignItems="center">
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    {game.player_faction.name.charAt(0)}
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1">
                      {game.player_faction.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {game.player_faction.type}
                    </Typography>
                  </Box>
                </Box>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="body2">
                  <strong>Influence:</strong> {game.player_faction.influence || 0}
                </Typography>
                <Typography variant="body2">
                  <strong>Resources:</strong> {game.player_faction.resources || 0}
                </Typography>
                <Typography variant="body2">
                  <strong>Supporters:</strong> {game.player_faction.supporters || 0}
                </Typography>
              </Paper>
              
              <Paper elevation={1} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Actions
                </Typography>
                <List dense>
                  <ListItem button onClick={() => setTabValue(1)}>
                    <ListItemText primary="View Faction Relations" />
                  </ListItem>
                  <ListItem button onClick={() => setTabValue(2)}>
                    <ListItemText primary="Manage Characters" />
                  </ListItem>
                  <ListItem button>
                    <ListItemText primary="Plan Operations" />
                  </ListItem>
                  <ListItem button>
                    <ListItemText primary="Manage Resources" />
                  </ListItem>
                </List>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h5" gutterBottom>
            Factions
          </Typography>
          
          <Grid container spacing={3}>
            {factions.length === 0 ? (
              <Grid item xs={12}>
                <Alert severity="info">
                  No faction data available.
                </Alert>
              </Grid>
            ) : (
              factions.map((faction) => (
                <Grid item xs={12} md={6} lg={4} key={faction.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={1}>
                        <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                          {faction.name.charAt(0)}
                        </Avatar>
                        <Typography variant="h6">
                          {faction.name}
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {faction.type} • {faction.ideology}
                      </Typography>
                      
                      <Divider sx={{ my: 1 }} />
                      
                      <Typography variant="body2">
                        <strong>Influence:</strong> {faction.game_data?.influence || 0}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Resources:</strong> {faction.game_data?.resources || 0}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Relationship:</strong> {faction.relationship || "Neutral"}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">
              Characters
            </Typography>
            <Button 
              variant="outlined"
              color="primary"
              onClick={() => navigate(`/games/${id}/characters/new`)}
            >
              Create Character
            </Button>
          </Box>
          
          <Grid container spacing={3}>
            {characters.length === 0 ? (
              <Grid item xs={12}>
                <Alert severity="info">
                  No characters created yet. Create a character to start building your network.
                </Alert>
              </Grid>
            ) : (
              characters.map((character) => (
                <Grid item xs={12} md={6} lg={4} key={character.id}>
                  <Card sx={{ cursor: 'pointer' }} onClick={() => handleCharacterClick(character.id)}>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={1}>
                        <Avatar sx={{ mr: 2 }}>
                          {character.name.charAt(0)}
                        </Avatar>
                        <Box>
                          <Typography variant="h6">
                            {character.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {character.role}
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Divider sx={{ my: 1 }} />
                      
                      <Typography variant="body2">
                        <strong>Skills:</strong> {character.skills?.join(', ') || 'None'}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Cells:</strong> {character.cells?.length || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h5" gutterBottom>
            Game Events
          </Typography>
          
          {events.length === 0 ? (
            <Alert severity="info">
              No events have occurred yet. Events will appear here as the game progresses.
            </Alert>
          ) : (
            <List>
              {events.map((event, index) => (
                <ListItem key={index} divider={index < events.length - 1}>
                  <ListItemIcon>
                    <NotificationsIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary={
                      <Typography variant="subtitle1">
                        {event.title}
                      </Typography>
                    }
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary">
                          Turn {event.turn} - {formatDate(event.date)}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 1 }}>
                          {event.description}
                        </Typography>
                      </>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </TabPanel>
      </Box>
      
      {/* Confirm Turn Advancement Dialog */}
      <Dialog
        open={confirmAdvanceTurn}
        onClose={() => setConfirmAdvanceTurn(false)}
      >
        <DialogTitle>Advance Turn?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to advance to turn {(game?.turn || 0) + 1}? 
            This will process all pending actions and generate new events.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmAdvanceTurn(false)}>Cancel</Button>
          <Button 
            onClick={handleAdvanceTurn} 
            color="primary"
            disabled={advancingTurn}
          >
            {advancingTurn ? 'Processing...' : 'Advance Turn'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GameDetail;
