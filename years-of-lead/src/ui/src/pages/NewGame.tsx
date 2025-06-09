import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField, 
  Button, 
  Grid, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  FormHelperText,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardMedia,
  CardActionArea
} from '@mui/material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useNavigate } from 'react-router-dom';
import { gameService, factionService } from '../services/api';

interface Scenario {
  id: string;
  name: string;
  description: string;
  year: number;
  difficulty: string;
  image_url?: string;
}

interface Faction {
  id: string;
  name: string;
  type: string;
  ideology: string;
  description: string;
  playable: boolean;
}

const NewGame: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [factions, setFactions] = useState<Faction[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // In a real implementation, we would fetch the actual scenarios and factions
        // For now, we'll use mock data
        const mockScenarios: Scenario[] = [
          {
            id: '1',
            name: 'Italian Social Crisis',
            description: 'Italy, 1969: The "Hot Autumn" labor disputes have sparked violent confrontations. Student protests and worker strikes across the country threaten political stability as extremist groups emerge on both the left and right.',
            year: 1969,
            difficulty: 'Medium',
            image_url: 'https://via.placeholder.com/400x200?text=Italy+1969'
          },
          {
            id: '2',
            name: 'Strategy of Tension',
            description: 'Italy, 1972: Following the Piazza Fontana bombing, the country is gripped by fear as political violence escalates. Secret services, international intelligence agencies, and extremist groups play a dangerous game of deception.',
            year: 1972,
            difficulty: 'Hard',
            image_url: 'https://via.placeholder.com/400x200?text=Italy+1972'
          },
          {
            id: '3',
            name: 'Years of Lead',
            description: 'Italy, 1975: The country is trapped in a spiral of violence. The Red Brigades have escalated their campaign of terror, while neo-fascist groups respond with their own attacks. The Italian state struggles to maintain control.',
            year: 1975,
            difficulty: 'Expert',
            image_url: 'https://via.placeholder.com/400x200?text=Italy+1975'
          }
        ];
        
        const mockFactions: Faction[] = [
          {
            id: '1',
            name: 'Red Brigades',
            type: 'Revolutionary Left',
            ideology: 'Communist',
            description: 'Marxist-Leninist militant organization focused on armed struggle against the capitalist state.',
            playable: true
          },
          {
            id: '2',
            name: 'Ordine Nuovo',
            type: 'Neo-Fascist',
            ideology: 'Far-right',
            description: 'Neo-fascist political movement aiming to restore a fascist state through revolutionary action.',
            playable: true
          },
          {
            id: '3',
            name: 'SISMI',
            type: 'State Intelligence',
            ideology: 'Government',
            description: 'Military Intelligence and Security Service, operating to maintain state security.',
            playable: true
          },
          {
            id: '4',
            name: 'CIA',
            type: 'Foreign Intelligence',
            ideology: 'Anti-Communist',
            description: 'American intelligence agency operating in Italy to counter communist influence.',
            playable: false
          }
        ];
        
        setScenarios(mockScenarios);
        setFactions(mockFactions.filter(f => f.playable));
        
        setLoading(false);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load required data');
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const formik = useFormik({
    initialValues: {
      name: '',
      scenarioId: '',
      factionId: '',
    },
    validationSchema: Yup.object({
      name: Yup.string()
        .min(3, 'Must be at least 3 characters')
        .max(50, 'Must be 50 characters or less')
        .required('Required'),
      scenarioId: Yup.string()
        .required('Please select a scenario'),
      factionId: Yup.string()
        .required('Please select a faction'),
    }),
    onSubmit: async (values) => {
      try {
        setSubmitting(true);
        setError(null);
        
        // In a real implementation, we would call the API
        // For now, we'll simulate a successful request
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Mock response
        const gameId = 'new-game-123';
        
        // Navigate to the new game
        navigate(`/games/${gameId}`);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to create game');
        setSubmitting(false);
      }
    },
  });

  const handleScenarioSelect = (scenarioId: string) => {
    formik.setFieldValue('scenarioId', scenarioId);
    setSelectedScenario(scenarios.find(s => s.id === scenarioId) || null);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Create New Game
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <form onSubmit={formik.handleSubmit}>
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Game Details
          </Typography>
          
          <TextField
            fullWidth
            id="name"
            name="name"
            label="Game Name"
            margin="normal"
            value={formik.values.name}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            error={formik.touched.name && Boolean(formik.errors.name)}
            helperText={formik.touched.name && formik.errors.name}
          />
        </Paper>

        <Typography variant="h6" gutterBottom>
          Select Scenario
        </Typography>
        {formik.touched.scenarioId && formik.errors.scenarioId && (
          <FormHelperText error>{formik.errors.scenarioId}</FormHelperText>
        )}
        
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {scenarios.map((scenario) => (
            <Grid item xs={12} md={4} key={scenario.id}>
              <Card 
                raised={formik.values.scenarioId === scenario.id} 
                sx={{ 
                  border: formik.values.scenarioId === scenario.id ? '2px solid' : 'none',
                  borderColor: 'primary.main'
                }}
              >
                <CardActionArea onClick={() => handleScenarioSelect(scenario.id)}>
                  <CardMedia
                    component="img"
                    height="140"
                    image={scenario.image_url || `https://via.placeholder.com/400x200?text=${encodeURIComponent(scenario.name)}`}
                    alt={scenario.name}
                  />
                  <CardContent>
                    <Typography gutterBottom variant="h5" component="div">
                      {scenario.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {scenario.year} • {scenario.difficulty}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {scenario.description.substring(0, 150)}
                      {scenario.description.length > 150 ? '...' : ''}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Typography variant="h6" gutterBottom>
          Select Faction
        </Typography>
        
        {formik.touched.factionId && formik.errors.factionId && (
          <FormHelperText error>{formik.errors.factionId}</FormHelperText>
        )}
        
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {factions.map((faction) => (
            <Grid item xs={12} md={4} key={faction.id}>
              <Card 
                raised={formik.values.factionId === faction.id}
                sx={{ 
                  border: formik.values.factionId === faction.id ? '2px solid' : 'none',
                  borderColor: 'primary.main'
                }}
                onClick={() => formik.setFieldValue('factionId', faction.id)}
              >
                <CardActionArea>
                  <CardContent>
                    <Typography gutterBottom variant="h5" component="div">
                      {faction.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {faction.type} • {faction.ideology}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {faction.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>

        {selectedScenario && formik.values.factionId && (
          <Box sx={{ mb: 4 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Game Summary
              </Typography>
              <Typography variant="body2">
                <strong>Game Name:</strong> {formik.values.name || "Untitled Game"}
              </Typography>
              <Typography variant="body2">
                <strong>Scenario:</strong> {selectedScenario.name} ({selectedScenario.year})
              </Typography>
              <Typography variant="body2">
                <strong>Faction:</strong> {factions.find(f => f.id === formik.values.factionId)?.name}
              </Typography>
            </Alert>
          </Box>
        )}

        <Box display="flex" justifyContent="space-between">
          <Button onClick={() => navigate('/games')} variant="outlined">
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            color="primary"
            disabled={submitting || !formik.isValid}
          >
            {submitting ? 'Creating Game...' : 'Create Game'}
          </Button>
        </Box>
      </form>
    </Box>
  );
};

export default NewGame;
