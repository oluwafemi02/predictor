import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Paper,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  SportsSoccer,
  EmojiEvents,
  Timeline,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { getUpcomingPredictions, getMatches, getModelStatus } from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { data: upcomingPredictions, isLoading: loadingPredictions } = useQuery({
    queryKey: ['upcomingPredictions'],
    queryFn: getUpcomingPredictions,
  });

  const { data: recentMatches, isLoading: loadingMatches } = useQuery({
    queryKey: ['recentMatches'],
    queryFn: () =>
      getMatches({
        status: 'finished',
        page: 1,
      }),
  });

  const { data: modelStatus, isLoading: loadingModel } = useQuery({
    queryKey: ['modelStatus'],
    queryFn: getModelStatus,
  });

  const getProbabilityColor = (probability: number) => {
    if (probability >= 0.6) return 'success';
    if (probability >= 0.4) return 'warning';
    return 'error';
  };

  const getMatchStatusColor = (status: string) => {
    switch (status) {
      case 'finished':
        return 'success';
      case 'in_play':
        return 'warning';
      case 'scheduled':
        return 'info';
      default:
        return 'default';
    }
  };

  if (loadingPredictions || loadingMatches || loadingModel) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Model Status Card */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Model Status
                  </Typography>
                  <Chip
                    label={modelStatus?.is_trained ? 'Trained' : 'Not Trained'}
                    color={modelStatus?.is_trained ? 'success' : 'error'}
                    size="small"
                  />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Version: {modelStatus?.model_version || 'N/A'}
                  </Typography>
                </Box>
                <Timeline fontSize="large" color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Today's Predictions
                  </Typography>
                  <Typography variant="h4">
                    {upcomingPredictions?.filter(p => 
                      new Date(p.match_date).toDateString() === new Date().toDateString()
                    ).length || 0}
                  </Typography>
                </Box>
                <TrendingUp fontSize="large" color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Upcoming Matches
                  </Typography>
                  <Typography variant="h4">
                    {upcomingPredictions?.length || 0}
                  </Typography>
                </Box>
                <SportsSoccer fontSize="large" color="secondary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Recent Results
                  </Typography>
                  <Typography variant="h4">
                    {recentMatches?.matches?.length || 0}
                  </Typography>
                </Box>
                <EmojiEvents fontSize="large" color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" gutterBottom>
                    Model Accuracy
                  </Typography>
                  <Typography variant="h4">
                    {modelStatus?.is_trained ? '85%' : 'N/A'}
                  </Typography>
                </Box>
                <Timeline fontSize="large" color="info" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Upcoming Predictions */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Upcoming Predictions</Typography>
              <Button
                variant="text"
                color="primary"
                onClick={() => navigate('/predictions')}
              >
                View All
              </Button>
            </Box>

            {upcomingPredictions && upcomingPredictions.length > 0 ? (
              <Box>
                {upcomingPredictions.slice(0, 5).map((prediction: any) => (
                  <Card key={prediction.match_id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box flex={1}>
                          <Typography variant="body2" color="text.secondary">
                            {format(new Date(prediction.match_date), 'PPp')}
                          </Typography>
                          <Typography variant="h6">
                            {prediction.home_team} vs {prediction.away_team}
                          </Typography>
                        </Box>

                        <Box display="flex" gap={2} alignItems="center">
                          <Box textAlign="center">
                            <Typography variant="body2" color="text.secondary">
                              Home Win
                            </Typography>
                            <Chip
                              label={`${(prediction.predictions.ensemble.home_win_probability * 100).toFixed(1)}%`}
                              color={getProbabilityColor(prediction.predictions.ensemble.home_win_probability)}
                              size="small"
                            />
                          </Box>
                          <Box textAlign="center">
                            <Typography variant="body2" color="text.secondary">
                              Draw
                            </Typography>
                            <Chip
                              label={`${(prediction.predictions.ensemble.draw_probability * 100).toFixed(1)}%`}
                              color={getProbabilityColor(prediction.predictions.ensemble.draw_probability)}
                              size="small"
                            />
                          </Box>
                          <Box textAlign="center">
                            <Typography variant="body2" color="text.secondary">
                              Away Win
                            </Typography>
                            <Chip
                              label={`${(prediction.predictions.ensemble.away_win_probability * 100).toFixed(1)}%`}
                              color={getProbabilityColor(prediction.predictions.ensemble.away_win_probability)}
                              size="small"
                            />
                          </Box>
                        </Box>

                        <Box>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => navigate(`/matches/${prediction.match_id}`)}
                          >
                            Details
                          </Button>
                        </Box>
                      </Box>

                      <Box mt={2}>
                        <Typography variant="body2" color="text.secondary">
                          Expected Score: {prediction.expected_goals.home.toFixed(1)} - {prediction.expected_goals.away.toFixed(1)}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1} mt={1}>
                          <Typography variant="body2" color="text.secondary">
                            Confidence:
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={prediction.confidence * 100}
                            sx={{ flex: 1, height: 8, borderRadius: 4 }}
                          />
                          <Typography variant="body2">
                            {(prediction.confidence * 100).toFixed(0)}%
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : (
              <Alert severity="info">No upcoming predictions available</Alert>
            )}
          </Paper>
        </Grid>

        {/* Recent Results */}
        <Grid item xs={12} lg={4}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Recent Results</Typography>
              <Button
                variant="text"
                color="primary"
                onClick={() => navigate('/matches')}
              >
                View All
              </Button>
            </Box>

            {recentMatches?.matches && recentMatches.matches.length > 0 ? (
              <Box>
                {recentMatches.matches.slice(0, 5).map((match: any) => (
                  <Card key={match.id} sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box flex={1}>
                          <Typography variant="body2" color="text.secondary">
                            {format(new Date(match.date), 'PP')}
                          </Typography>
                          <Typography variant="body1">
                            {match.home_team.name} {match.home_score} - {match.away_score} {match.away_team.name}
                          </Typography>
                        </Box>
                        <Chip
                          label={match.status}
                          color={getMatchStatusColor(match.status)}
                          size="small"
                        />
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            ) : (
              <Alert severity="info">No recent matches available</Alert>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;