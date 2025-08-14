import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Paper,
  LinearProgress,
  Divider,
  Grid,
  Container,
  useTheme,
  useMediaQuery,
  alpha,
  IconButton,
  Tooltip,
  Skeleton,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { format, startOfDay, endOfDay, addDays } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  SportsSoccer,
  Assessment,
  MoneyOff,
  FilterList,
  Refresh,
  CalendarToday,
  AccessTime,
  Stadium,
  EmojiEvents,
  ArrowForward,
} from '@mui/icons-material';
import { getPredictions, getCompetitions, getUpcomingPredictions } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';

const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  
  const [dateFrom, setDateFrom] = useState<Date | null>(new Date());
  const [dateTo, setDateTo] = useState<Date | null>(addDays(new Date(), 7));
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(!isMobile);

  const { data: competitions } = useQuery({
    queryKey: ['competitions'],
    queryFn: getCompetitions,
  });

  // Fetch upcoming predictions
  const { data: upcomingPredictions, isLoading: loadingUpcoming, refetch: refetchUpcoming } = useQuery({
    queryKey: ['upcomingPredictions'],
    queryFn: getUpcomingPredictions,
  });

  // Fetch filtered predictions
  const { data: predictionsData, isLoading, refetch } = useQuery({
    queryKey: ['predictions', dateFrom, dateTo, page, selectedCompetition],
    queryFn: () =>
      getPredictions({
        date_from: dateFrom ? format(startOfDay(dateFrom), 'yyyy-MM-dd') : undefined,
        date_to: dateTo ? format(endOfDay(dateTo), 'yyyy-MM-dd') : undefined,
        page,
        competition: selectedCompetition || undefined,
      }),
  });

  const handleRefresh = () => {
    refetch();
    refetchUpcoming();
  };

  const getProbabilityColor = (probability: number) => {
    if (probability >= 0.6) return 'success';
    if (probability >= 0.4) return 'warning';
    return 'error';
  };

  const formatProbability = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const renderProbabilityChart = (prediction: any) => {
    const data = [
      { name: 'Home Win', value: (prediction.prediction?.home_win || prediction.predictions?.ensemble?.home_win_probability || 0) * 100 },
      { name: 'Draw', value: (prediction.prediction?.draw || prediction.predictions?.ensemble?.draw_probability || 0) * 100 },
      { name: 'Away Win', value: (prediction.prediction?.away_win || prediction.predictions?.ensemble?.away_win_probability || 0) * 100 },
    ];

    const COLORS = [theme.palette.success.main, theme.palette.warning.main, theme.palette.error.main];

    return (
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ value }) => `${value.toFixed(1)}%`}
            outerRadius={70}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <RechartsTooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  if (isLoading || loadingUpcoming) {
    return (
      <Container maxWidth="xl">
        <Box>
          <Skeleton variant="text" width={300} height={60} sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Grid item xs={12} md={6} lg={4} key={i}>
                <Skeleton variant="rounded" height={320} />
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>
    );
  }

  // Combine upcoming predictions with filtered predictions
  const allPredictions = [
    ...(upcomingPredictions || []),
    ...(predictionsData?.predictions || [])
  ].filter((prediction, index, self) => 
    index === self.findIndex((p) => 
      (p.match_id || p.id) === (prediction.match_id || prediction.id)
    )
  );

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
          <Box>
            <Typography variant="h3" gutterBottom fontWeight="bold">
              Match Predictions
            </Typography>
            <Typography variant="body1" color="text.secondary">
              AI-powered predictions for upcoming football matches
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Tooltip title="Toggle Filters">
              <IconButton
                onClick={() => setShowFilters(!showFilters)}
                color="primary"
                sx={{
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  },
                }}
              >
                <FilterList />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh Predictions">
              <IconButton
                onClick={handleRefresh}
                color="primary"
                sx={{
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  },
                }}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Quick Stats */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={6} sm={3}>
            <Paper
              sx={{
                p: 2,
                textAlign: 'center',
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.primary.dark, 0.1)} 100%)`,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
              }}
            >
              <SportsSoccer sx={{ fontSize: 32, color: theme.palette.primary.main, mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {allPredictions.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Predictions
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper
              sx={{
                p: 2,
                textAlign: 'center',
                background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.1)} 0%, ${alpha(theme.palette.info.dark, 0.1)} 100%)`,
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
              }}
            >
              <CalendarToday sx={{ fontSize: 32, color: theme.palette.info.main, mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {allPredictions.filter(p => {
                  const matchDate = new Date(p.match_date || p.match?.date);
                  return matchDate.toDateString() === new Date().toDateString();
                }).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Today's Matches
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper
              sx={{
                p: 2,
                textAlign: 'center',
                background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)} 0%, ${alpha(theme.palette.success.dark, 0.1)} 100%)`,
                border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`,
              }}
            >
              <TrendingUp sx={{ fontSize: 32, color: theme.palette.success.main, mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {allPredictions.filter(p => {
                  const confidence = p.prediction?.confidence || p.predictions?.ensemble?.confidence || 0;
                  return confidence > 0.7;
                }).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                High Confidence
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={6} sm={3}>
            <Paper
              sx={{
                p: 2,
                textAlign: 'center',
                background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.dark, 0.1)} 100%)`,
                border: `1px solid ${alpha(theme.palette.secondary.main, 0.2)}`,
              }}
            >
              <EmojiEvents sx={{ fontSize: 32, color: theme.palette.secondary.main, mb: 1 }} />
              <Typography variant="h4" fontWeight="bold">
                {competitions?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Competitions
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Filters */}
        {showFilters && (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom fontWeight="600">
              Filter Predictions
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="From Date"
                  value={dateFrom}
                  onChange={setDateFrom}
                  slotProps={{ 
                    textField: { 
                      fullWidth: true,
                      size: isMobile ? 'small' : 'medium',
                    } 
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <DatePicker
                  label="To Date"
                  value={dateTo}
                  onChange={setDateTo}
                  slotProps={{ 
                    textField: { 
                      fullWidth: true,
                      size: isMobile ? 'small' : 'medium',
                    } 
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size={isMobile ? 'small' : 'medium'}>
                  <InputLabel>Competition</InputLabel>
                  <Select
                    value={selectedCompetition}
                    onChange={(e) => setSelectedCompetition(e.target.value)}
                    label="Competition"
                  >
                    <MenuItem value="">All Competitions</MenuItem>
                    {competitions?.map((comp) => (
                      <MenuItem key={comp} value={comp}>
                        {comp}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button 
                  variant="contained" 
                  fullWidth 
                  onClick={() => setPage(1)}
                  size={isMobile ? 'small' : 'medium'}
                  startIcon={<FilterList />}
                >
                  Apply Filters
                </Button>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* Predictions Grid */}
        {allPredictions && allPredictions.length > 0 ? (
          <Grid container spacing={3}>
            {allPredictions.map((prediction: any) => {
              const match = prediction.match || {
                id: prediction.match_id,
                date: prediction.match_date,
                home_team: { name: prediction.home_team },
                away_team: { name: prediction.away_team },
                venue: prediction.venue,
                status: prediction.status || 'scheduled',
              };
              
              const predictionData = prediction.prediction || prediction.predictions?.ensemble || {};
              const confidence = predictionData.confidence || prediction.confidence || 0.75;
              
              return (
                <Grid item xs={12} md={6} lg={4} key={prediction.id || prediction.match_id}>
                  <Card
                    sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                      },
                    }}
                    onClick={() => navigate(`/matches/${match.id}`)}
                  >
                    <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                      {/* Match Header */}
                      <Box mb={2}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Chip
                            icon={<AccessTime />}
                            label={format(new Date(match.date), 'MMM d, yyyy')}
                            color="primary"
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {format(new Date(match.date), 'HH:mm')}
                          </Typography>
                        </Box>
                        
                        <Typography variant="h6" fontWeight="600" gutterBottom>
                          {match.home_team.name}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color="text.secondary" 
                          sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            my: 1,
                          }}
                        >
                          VS
                        </Typography>
                        <Typography variant="h6" fontWeight="600" gutterBottom>
                          {match.away_team.name}
                        </Typography>
                        
                        {match.venue && (
                          <Box display="flex" alignItems="center" gap={0.5} mt={1}>
                            <Stadium fontSize="small" sx={{ color: theme.palette.text.secondary }} />
                            <Typography variant="caption" color="text.secondary">
                              {match.venue}
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      {/* Prediction Chart */}
                      <Box sx={{ flex: 1 }}>
                        {renderProbabilityChart(prediction)}
                      </Box>

                      <Divider sx={{ my: 2 }} />

                      {/* Score Prediction */}
                      {(predictionData.predicted_score || prediction.expected_goals) && (
                        <Box mb={2}>
                          <Typography variant="subtitle2" gutterBottom color="text.secondary">
                            <SportsSoccer sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                            Predicted Score
                          </Typography>
                          <Typography variant="h5" textAlign="center" fontWeight="600">
                            {predictionData.predicted_score?.home || prediction.expected_goals?.home?.toFixed(0) || 0} - {' '}
                            {predictionData.predicted_score?.away || prediction.expected_goals?.away?.toFixed(0) || 0}
                          </Typography>
                        </Box>
                      )}

                      {/* Confidence Score */}
                      <Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                          <Typography variant="subtitle2" color="text.secondary">
                            <Assessment sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                            Confidence Score
                          </Typography>
                          <Typography variant="body2" fontWeight="600">
                            {formatProbability(confidence)}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={confidence * 100}
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            backgroundColor: alpha(theme.palette.primary.main, 0.1),
                          }}
                          color={
                            confidence > 0.7
                              ? 'success'
                              : confidence > 0.5
                              ? 'warning'
                              : 'error'
                          }
                        />
                      </Box>

                      {/* Action Button */}
                      <Box mt={3}>
                        <Button
                          variant="outlined"
                          fullWidth
                          endIcon={<ArrowForward />}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/matches/${match.id}`);
                          }}
                        >
                          View Details
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        ) : (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <SportsSoccer sx={{ fontSize: 64, color: theme.palette.text.secondary, mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No predictions found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Try adjusting your filters or check back later for new predictions
            </Typography>
            <Button variant="contained" onClick={handleRefresh} startIcon={<Refresh />}>
              Refresh
            </Button>
          </Paper>
        )}

        {/* Pagination */}
        {predictionsData?.pagination && predictionsData.pagination.pages > 1 && (
          <Box display="flex" justifyContent="center" alignItems="center" mt={4} gap={2}>
            <Button
              variant="outlined"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              size={isMobile ? 'small' : 'medium'}
            >
              Previous
            </Button>
            <Typography sx={{ display: 'flex', alignItems: 'center' }}>
              Page {page} of {predictionsData.pagination.pages}
            </Typography>
            <Button
              variant="outlined"
              disabled={page === predictionsData.pagination.pages}
              onClick={() => setPage(page + 1)}
              size={isMobile ? 'small' : 'medium'}
            >
              Next
            </Button>
          </Box>
        )}
      </Box>
    </Container>
  );
};

export default Predictions;