import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
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
  Grid,
  Divider,
  Container,
  IconButton,
  useTheme,
  useMediaQuery,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  SportsSoccer,
  EmojiEvents,
  Timeline,
  CalendarToday,
  Stadium,
  ArrowForward,
  AccessTime,
  Psychology,
  CheckCircle,
  Pending,
} from '@mui/icons-material';
import { format, isToday, isTomorrow, isThisWeek } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { getUpcomingPredictions, getMatches, getModelStatus, getUpcomingMatches } from '../services/api';
import MainPagePredictions from '../components/MainPagePredictions';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  const { data: upcomingPredictions, isLoading: loadingPredictions } = useQuery({
    queryKey: ['upcomingPredictions'],
    queryFn: getUpcomingPredictions,
  });

  const { data: upcomingMatches, isLoading: loadingUpcoming } = useQuery({
    queryKey: ['upcomingMatches'],
    queryFn: () => getUpcomingMatches(15),
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

  const getDateLabel = (date: string) => {
    const matchDate = new Date(date);
    if (isToday(matchDate)) return 'Today';
    if (isTomorrow(matchDate)) return 'Tomorrow';
    if (isThisWeek(matchDate)) return format(matchDate, 'EEEE');
    return format(matchDate, 'MMM d');
  };

  const formatProbability = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loadingPredictions || loadingMatches || loadingModel || loadingUpcoming) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ pb: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" gutterBottom fontWeight="bold">
          Football Predictions Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time match predictions powered by advanced AI models
        </Typography>
      </Box>

      {/* Model Status Card */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Card 
            sx={{ 
              background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
              border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={2}>
                <Box display="flex" alignItems="center" gap={2}>
                  <Box
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Psychology fontSize="large" sx={{ color: theme.palette.primary.main }} />
                  </Box>
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      AI Model Status
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        icon={modelStatus?.is_trained ? <CheckCircle /> : <Pending />}
                        label={modelStatus?.is_trained ? 'Trained & Ready' : 'Training Required'}
                        color={modelStatus?.is_trained ? 'success' : 'error'}
                        size="small"
                      />
                      <Typography variant="body2" color="text.secondary">
                        Version: {modelStatus?.model_version || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                <Button
                  variant="outlined"
                  color="primary"
                  endIcon={<ArrowForward />}
                  onClick={() => navigate('/model-status')}
                >
                  View Details
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Today's Predictions
                  </Typography>
                  <Typography variant="h3" fontWeight="bold">
                    {upcomingPredictions?.filter(p => 
                      new Date(p.match?.date || '').toDateString() === new Date().toDateString()
                    ).length || 0}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  }}
                >
                  <TrendingUp sx={{ fontSize: 28, color: theme.palette.primary.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Upcoming Matches
                  </Typography>
                  <Typography variant="h3" fontWeight="bold">
                    {upcomingMatches?.length || 0}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.info.main, 0.1),
                  }}
                >
                  <CalendarToday sx={{ fontSize: 28, color: theme.palette.info.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Recent Results
                  </Typography>
                  <Typography variant="h3" fontWeight="bold">
                    {recentMatches?.matches?.length || 0}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.success.main, 0.1),
                  }}
                >
                  <EmojiEvents sx={{ fontSize: 28, color: theme.palette.success.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2" gutterBottom>
                    Active Predictions
                  </Typography>
                  <Typography variant="h3" fontWeight="bold">
                    {upcomingPredictions?.length || 0}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: alpha(theme.palette.secondary.main, 0.1),
                  }}
                >
                  <Timeline sx={{ fontSize: 28, color: theme.palette.secondary.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Enhanced AI Predictions Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, background: alpha(theme.palette.background.paper, 0.5) }}>
            <MainPagePredictions />
          </Paper>
        </Grid>
      </Grid>

      {/* Upcoming Matches Section */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Box display="flex" alignItems="center" gap={1}>
                <CalendarToday sx={{ color: theme.palette.info.main }} />
                <Typography variant="h5" fontWeight="bold">
                  Upcoming Matches
                </Typography>
              </Box>
              <Button
                variant="outlined"
                color="info"
                endIcon={<ArrowForward />}
                onClick={() => navigate('/matches')}
                size={isMobile ? 'small' : 'medium'}
              >
                View All
              </Button>
            </Box>

            {upcomingMatches && upcomingMatches.length > 0 ? (
              <Grid container spacing={2}>
                {upcomingMatches.slice(0, 6).map((match: any) => (
                  <Grid item xs={12} sm={6} lg={4} key={match.id}>
                    <Card 
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        '&:hover': {
                          borderColor: theme.palette.primary.main,
                          backgroundColor: alpha(theme.palette.primary.main, 0.02),
                        },
                      }}
                      onClick={() => navigate(`/matches/${match.id}`)}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                          <Chip 
                            label={getDateLabel(match.date)} 
                            size="small" 
                            color="info" 
                            variant="outlined" 
                          />
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(match.date), 'HH:mm')}
                          </Typography>
                        </Box>
                        <Typography variant="body1" fontWeight="bold" gutterBottom>
                          {match.home_team.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          vs
                        </Typography>
                        <Typography variant="body1" fontWeight="bold" gutterBottom>
                          {match.away_team.name}
                        </Typography>
                        {match.venue && (
                          <Box display="flex" alignItems="center" gap={0.5} mt={2}>
                            <Stadium fontSize="small" sx={{ color: theme.palette.text.secondary }} />
                            <Typography variant="caption" color="text.secondary">
                              {match.venue}
                            </Typography>
                          </Box>
                        )}
                        <Box mt={2}>
                          <Chip 
                            label={match.competition || 'League'} 
                            size="small" 
                            variant="filled"
                            sx={{ 
                              backgroundColor: alpha(theme.palette.info.main, 0.1),
                              color: theme.palette.info.main,
                            }}
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Alert severity="info" icon={<CalendarToday />}>
                No upcoming matches scheduled at the moment
              </Alert>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Results Section */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5" fontWeight="bold">
                Recent Results
              </Typography>
            </Box>

            {recentMatches?.matches && recentMatches.matches.length > 0 ? (
              <Box sx={{ overflowX: 'auto' }}>
                {recentMatches.matches.slice(0, 5).map((match: any) => (
                  <Box
                    key={match.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      p: 2,
                      borderRadius: 2,
                      mb: 1,
                      backgroundColor: alpha(theme.palette.background.default, 0.5),
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: alpha(theme.palette.background.default, 0.8),
                      },
                    }}
                    onClick={() => navigate(`/matches/${match.id}`)}
                  >
                    <Box display="flex" alignItems="center" gap={2} flex={1}>
                      <Chip
                        label={getMatchStatusColor(match.status) === 'success' ? 'FT' : match.status}
                        color={getMatchStatusColor(match.status) as any}
                        size="small"
                      />
                      <Box flex={1}>
                        <Typography variant="body2">
                          {match.home_team.name} {match.home_score} - {match.away_score} {match.away_team.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {format(new Date(match.date), 'PPp')}
                        </Typography>
                      </Box>
                    </Box>
                    <IconButton size="small">
                      <ArrowForward fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
              </Box>
            ) : (
              <Alert severity="info">No recent match results available</Alert>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;