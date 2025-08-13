import React, { useState } from 'react';
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
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { format, startOfDay, endOfDay } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  SportsSoccer,
  Assessment,
  MoneyOff,
} from '@mui/icons-material';
import { getPredictions, getCompetitions } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const [dateFrom, setDateFrom] = useState<Date | null>(new Date());
  const [dateTo, setDateTo] = useState<Date | null>(
    new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  );
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [page, setPage] = useState(1);

  const { data: competitions } = useQuery({
    queryKey: ['competitions'],
    queryFn: getCompetitions,
  });

  const { data: predictionsData, isLoading } = useQuery({
    queryKey: ['predictions', dateFrom, dateTo, page],
    queryFn: () =>
      getPredictions({
        date_from: dateFrom ? format(startOfDay(dateFrom), 'yyyy-MM-dd') : undefined,
        date_to: dateTo ? format(endOfDay(dateTo), 'yyyy-MM-dd') : undefined,
        page,
      }),
  });

  const getProbabilityColor = (probability: number) => {
    if (probability >= 0.6) return 'success';
    if (probability >= 0.4) return 'warning';
    return 'error';
  };

  const renderProbabilityChart = (prediction: any) => {
    const data = [
      { name: 'Home Win', value: (prediction.prediction?.home_win || 0) * 100 },
      { name: 'Draw', value: (prediction.prediction?.draw || 0) * 100 },
      { name: 'Away Win', value: (prediction.prediction?.away_win || 0) * 100 },
    ];

    const COLORS = ['#4CAF50', '#FF9800', '#f44336'];

    return (
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ value }) => `${value.toFixed(1)}%`}
            outerRadius={80}
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Match Predictions
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4} md={3}>
            <DatePicker
              label="From Date"
              value={dateFrom}
              onChange={setDateFrom}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <DatePicker
              label="To Date"
              value={dateTo}
              onChange={setDateTo}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth>
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
          <Grid item xs={12} sm={12} md={3}>
            <Button variant="contained" fullWidth onClick={() => setPage(1)}>
              Apply Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Predictions Grid */}
      {predictionsData?.predictions && predictionsData.predictions.length > 0 ? (
        <Grid container spacing={3}>
          {predictionsData.predictions.map((prediction: any) => (
            <Grid item xs={12} md={6} key={prediction.id}>
              <Card>
                <CardContent>
                  {/* Match Header */}
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" color="text.secondary">
                        {format(new Date(prediction.match.date), 'PPp')}
                      </Typography>
                      <Chip
                        label={prediction.match.status || 'scheduled'}
                        color="info"
                        size="small"
                      />
                    </Box>
                    <Typography variant="h6" sx={{ mt: 1 }}>
                      {prediction.match.home_team.name} vs {prediction.match.away_team.name}
                    </Typography>
                    {prediction.match.venue && (
                      <Typography variant="body2" color="text.secondary">
                        {prediction.match.venue}
                      </Typography>
                    )}
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Prediction Chart */}
                  <Box>{renderProbabilityChart(prediction)}</Box>

                  <Divider sx={{ my: 2 }} />

                  {/* Score Prediction */}
                  <Box mb={2}>
                    <Typography variant="subtitle2" gutterBottom>
                      <SportsSoccer sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                      Predicted Score
                    </Typography>
                    <Typography variant="h5" textAlign="center">
                      {prediction.prediction?.predicted_score?.home || 0} -{' '}
                      {prediction.prediction?.predicted_score?.away || 0}
                    </Typography>
                  </Box>

                  {/* Confidence Score */}
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle2">
                        <Assessment sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
                        Confidence Score
                      </Typography>
                      <Typography variant="body2">
                        {((prediction.prediction?.confidence || 0.75) * 100).toFixed(0)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(prediction.prediction?.confidence || 0.75) * 100}
                      sx={{ height: 8, borderRadius: 4 }}
                      color={
                        (prediction.prediction?.confidence || 0.75) > 0.7
                          ? 'success'
                          : (prediction.prediction?.confidence || 0.75) > 0.5
                          ? 'warning'
                          : 'error'
                      }
                    />
                  </Box>

                  {/* Action Button */}
                  <Box mt={2}>
                    <Button
                      variant="outlined"
                      fullWidth
                      onClick={() => navigate(`/matches/${prediction.match.id}`)}
                    >
                      View Match Details
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info">No predictions found for the selected criteria</Alert>
      )}

      {/* Pagination */}
      {predictionsData?.pagination && predictionsData.pagination.pages > 1 && (
        <Box display="flex" justifyContent="center" mt={4}>
          <Button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            sx={{ mx: 1 }}
          >
            Previous
          </Button>
          <Typography sx={{ mx: 2, display: 'flex', alignItems: 'center' }}>
            Page {page} of {predictionsData.pagination.pages}
          </Typography>
          <Button
            disabled={page === predictionsData.pagination.pages}
            onClick={() => setPage(page + 1)}
            sx={{ mx: 1 }}
          >
            Next
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default Predictions;