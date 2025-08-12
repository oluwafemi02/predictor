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
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Avatar,
  IconButton,
  Tooltip,
  Grid,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { format, startOfDay, endOfDay } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import {
  Visibility,
  QueryStats,
  SportsSoccer,
} from '@mui/icons-material';
import { getMatches, getCompetitions, getTeams } from '../services/api';

const Matches: React.FC = () => {
  const navigate = useNavigate();
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [selectedTeam, setSelectedTeam] = useState<number | ''>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [page, setPage] = useState(1);

  const { data: competitions } = useQuery({
    queryKey: ['competitions'],
    queryFn: getCompetitions,
  });

  const { data: teams } = useQuery({
    queryKey: ['teams', selectedCompetition],
    queryFn: () => getTeams(selectedCompetition),
  });

  const { data: matchesData, isLoading, refetch } = useQuery({
    queryKey: ['matches', dateFrom, dateTo, selectedCompetition, selectedTeam, selectedStatus, page],
    queryFn: () =>
      getMatches({
        date_from: dateFrom ? format(startOfDay(dateFrom), 'yyyy-MM-dd') : undefined,
        date_to: dateTo ? format(endOfDay(dateTo), 'yyyy-MM-dd') : undefined,
        competition: selectedCompetition || undefined,
        team_id: selectedTeam || undefined,
        status: selectedStatus || undefined,
        page,
      }),
  });

  const getMatchStatusColor = (status: string) => {
    switch (status) {
      case 'finished':
        return 'success';
      case 'in_play':
        return 'warning';
      case 'scheduled':
        return 'info';
      case 'postponed':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleApplyFilters = () => {
    setPage(1);
    refetch();
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
        Matches
      </Typography>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={2}>
            <DatePicker
              label="From Date"
              value={dateFrom}
              onChange={setDateFrom}
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <DatePicker
              label="To Date"
              value={dateTo}
              onChange={setDateTo}
              slotProps={{ textField: { fullWidth: true, size: 'small' } }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
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
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Team</InputLabel>
              <Select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value as number)}
                label="Team"
              >
                <MenuItem value="">All Teams</MenuItem>
                {teams?.map((team) => (
                  <MenuItem key={team.id} value={team.id}>
                    {team.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                label="Status"
              >
                <MenuItem value="">All Status</MenuItem>
                <MenuItem value="scheduled">Scheduled</MenuItem>
                <MenuItem value="in_play">In Play</MenuItem>
                <MenuItem value="finished">Finished</MenuItem>
                <MenuItem value="postponed">Postponed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <Button variant="contained" fullWidth onClick={handleApplyFilters}>
              Apply Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Matches Table */}
      {matchesData?.matches && matchesData.matches.length > 0 ? (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date & Time</TableCell>
                  <TableCell>Competition</TableCell>
                  <TableCell>Home Team</TableCell>
                  <TableCell align="center">Score</TableCell>
                  <TableCell>Away Team</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Venue</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {matchesData.matches.map((match) => (
                  <TableRow key={match.id} hover>
                    <TableCell>
                      <Typography variant="body2">
                        {format(new Date(match.date), 'PP')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {format(new Date(match.date), 'p')}
                      </Typography>
                    </TableCell>
                    <TableCell>{match.competition}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {match.home_team.logo_url && (
                          <Avatar
                            src={match.home_team.logo_url}
                            sx={{ width: 24, height: 24 }}
                          />
                        )}
                        <Typography>{match.home_team.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      {match.status === 'finished' || match.status === 'in_play' ? (
                        <Typography variant="h6">
                          {match.home_score} - {match.away_score}
                        </Typography>
                      ) : (
                        <Typography color="text.secondary">vs</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {match.away_team.logo_url && (
                          <Avatar
                            src={match.away_team.logo_url}
                            sx={{ width: 24, height: 24 }}
                          />
                        )}
                        <Typography>{match.away_team.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={match.status}
                        color={getMatchStatusColor(match.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                        {match.venue || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/matches/${match.id}`)}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      {match.has_prediction && (
                        <Tooltip title="View Prediction">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => navigate(`/matches/${match.id}?tab=prediction`)}
                          >
                            <QueryStats />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {matchesData.pagination && matchesData.pagination.pages > 1 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                sx={{ mx: 1 }}
              >
                Previous
              </Button>
              <Typography sx={{ mx: 2, display: 'flex', alignItems: 'center' }}>
                Page {page} of {matchesData.pagination.pages} (Total: {matchesData.pagination.total} matches)
              </Typography>
              <Button
                disabled={page === matchesData.pagination.pages}
                onClick={() => setPage(page + 1)}
                sx={{ mx: 1 }}
              >
                Next
              </Button>
            </Box>
          )}
        </>
      ) : (
        <Alert severity="info">No matches found for the selected criteria</Alert>
      )}
    </Box>
  );
};

export default Matches;