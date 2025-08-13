import React, { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  Button,
  Tabs,
  Tab,
  Avatar,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import {
  SportsSoccer,
  Timeline,
  QueryStats,
  History,
  Groups,
  ArrowBack,
  Stadium,
  Person,
  PeopleAlt,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { getMatchDetails } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

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
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MatchDetails: React.FC = () => {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const defaultTab = searchParams.get('tab') === 'prediction' ? 1 : 0;
  const [tabValue, setTabValue] = useState(defaultTab);

  const { data, isLoading, error } = useQuery({
    queryKey: ['matchDetails', matchId],
    queryFn: () => getMatchDetails(parseInt(matchId || '0')),
    enabled: !!matchId,
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getFormColor = (result: string) => {
    switch (result) {
      case 'W': return 'success';
      case 'D': return 'warning';
      case 'L': return 'error';
      default: return 'default';
    }
  };

  const renderProbabilityChart = (prediction: any) => {
    if (!prediction) return null;

    const data = [
      { name: 'Home Win', value: prediction.home_win_probability * 100 },
      { name: 'Draw', value: prediction.draw_probability * 100 },
      { name: 'Away Win', value: prediction.away_win_probability * 100 },
    ];

    const COLORS = ['#4CAF50', '#FF9800', '#f44336'];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ value }) => `${value.toFixed(1)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/matches')}
          sx={{ mb: 2 }}
        >
          Back to Matches
        </Button>
        <Alert severity="error">Failed to load match details</Alert>
      </Box>
    );
  }

  const { match, prediction, head_to_head, team_form } = data;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Match Details</Typography>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/matches')}
        >
          Back to Matches
        </Button>
      </Box>

      {/* Match Summary Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={5} textAlign="center">
              <Box display="flex" alignItems="center" justifyContent="center" gap={2}>
                {match.home_team.logo_url && (
                  <Avatar
                    src={match.home_team.logo_url}
                    sx={{ width: 60, height: 60 }}
                  />
                )}
                <Box>
                  <Typography variant="h5">{match.home_team.name}</Typography>
                  {team_form?.home_team?.form && (
                    <Box display="flex" gap={0.5} justifyContent="center" mt={1}>
                      {team_form.home_team.form.split('').map((result: string, idx: number) => (
                        <Chip
                          key={idx}
                          label={result}
                          size="small"
                          color={getFormColor(result)}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </Box>
            </Grid>

            <Grid item xs={12} md={2} textAlign="center">
              {match.status === 'finished' ? (
                <Typography variant="h3">
                  {match.home_score} - {match.away_score}
                </Typography>
              ) : (
                <Typography variant="h4" color="text.secondary">
                  VS
                </Typography>
              )}
              {match.status === 'finished' && match.home_score_halftime !== null && (
                <Typography variant="body2" color="text.secondary">
                  HT: {match.home_score_halftime} - {match.away_score_halftime}
                </Typography>
              )}
              <Chip
                label={match.status}
                color={match.status === 'finished' ? 'success' : 'info'}
                size="small"
                sx={{ mt: 1 }}
              />
            </Grid>

            <Grid item xs={12} md={5} textAlign="center">
              <Box display="flex" alignItems="center" justifyContent="center" gap={2}>
                <Box>
                  <Typography variant="h5">{match.away_team.name}</Typography>
                  {team_form?.away_team?.form && (
                    <Box display="flex" gap={0.5} justifyContent="center" mt={1}>
                      {team_form.away_team.form.split('').map((result: string, idx: number) => (
                        <Chip
                          key={idx}
                          label={result}
                          size="small"
                          color={getFormColor(result)}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
                {match.away_team.logo_url && (
                  <Avatar
                    src={match.away_team.logo_url}
                    sx={{ width: 60, height: 60 }}
                  />
                )}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <SportsSoccer color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Competition: {match.competition}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <History color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Date: {format(new Date(match.date), 'PPp')}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Stadium color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Venue: {match.venue || 'TBD'}
                    </Typography>
                  </Box>
                </Grid>
                {match.referee && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Person color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Referee: {match.referee}
                      </Typography>
                    </Box>
                  </Grid>
                )}
                {match.attendance && (
                  <Grid item xs={12} sm={6} md={3}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <PeopleAlt color="action" />
                      <Typography variant="body2" color="text.secondary">
                        Attendance: {match.attendance.toLocaleString()}
                      </Typography>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="match details tabs">
          <Tab icon={<Timeline />} label="Head to Head" />
          {prediction && <Tab icon={<QueryStats />} label="Prediction Analysis" />}
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        {/* Head to Head Stats */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Overall H2H Stats
                </Typography>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Matches: {head_to_head?.total_matches || 0}
                  </Typography>
                  <Box mt={2}>
                    <Grid container spacing={1}>
                      <Grid item xs={4} textAlign="center">
                        <Typography variant="h4" color="success.main">
                          {head_to_head?.home_wins || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {match.home_team.name} Wins
                        </Typography>
                      </Grid>
                      <Grid item xs={4} textAlign="center">
                        <Typography variant="h4" color="warning.main">
                          {head_to_head?.draws || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Draws
                        </Typography>
                      </Grid>
                      <Grid item xs={4} textAlign="center">
                        <Typography variant="h4" color="error.main">
                          {head_to_head?.away_wins || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {match.away_team.name} Wins
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Recent H2H Matches
                </Typography>
                {head_to_head?.last_5_results && head_to_head.last_5_results.length > 0 ? (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell>Home</TableCell>
                          <TableCell align="center">Score</TableCell>
                          <TableCell>Away</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {head_to_head.last_5_results.map((result: any, idx: number) => (
                          <TableRow key={idx}>
                            <TableCell>
                              {format(new Date(result.date), 'PP')}
                            </TableCell>
                            <TableCell>{result.home_team}</TableCell>
                            <TableCell align="center">
                              <strong>{result.score}</strong>
                            </TableCell>
                            <TableCell>{result.away_team}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">No previous matches between these teams</Alert>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {/* Prediction Analysis */}
        {prediction && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Match Outcome Probabilities
                  </Typography>
                  {renderProbabilityChart(prediction)}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Prediction Details
                  </Typography>
                  
                  <Box mb={3}>
                    <Typography variant="subtitle2" gutterBottom>
                      Predicted Score
                    </Typography>
                    <Typography variant="h4" textAlign="center">
                      {prediction.predicted_home_score} - {prediction.predicted_away_score}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">Over 2.5 Goals</Typography>
                      <Typography variant="body2">
                        {(prediction.over_2_5_probability * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={prediction.over_2_5_probability * 100}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">Both Teams to Score</Typography>
                      <Typography variant="body2">
                        {(prediction.both_teams_score_probability * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={prediction.both_teams_score_probability * 100}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">Confidence Level</Typography>
                      <Typography variant="body2">
                        {(prediction.confidence_score * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={prediction.confidence_score * 100}
                      sx={{ height: 8, borderRadius: 4 }}
                      color={
                        prediction.confidence_score > 0.7
                          ? 'success'
                          : prediction.confidence_score > 0.5
                          ? 'warning'
                          : 'error'
                      }
                    />
                  </Box>

                  {prediction.factors && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Key Factors
                      </Typography>
                      <Box>
                        {Object.entries(prediction.factors).map(([key, value]) => (
                          <Box key={key} display="flex" justifyContent="space-between" py={0.5}>
                            <Typography variant="body2" color="text.secondary">
                              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                            </Typography>
                            <Typography variant="body2">
                              {value as string}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>
    </Box>
  );
};

export default MatchDetails;