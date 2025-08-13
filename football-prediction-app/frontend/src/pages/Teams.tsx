import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Grid,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
} from '@mui/material';
import { Search, SportsSoccer, Stadium, EmojiEvents } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getTeams, getCompetitions, TeamWithStats } from '../services/api';

type OrderBy = 'name' | 'points' | 'wins' | 'goals_for' | 'goal_difference';
type Order = 'asc' | 'desc';

const Teams: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCompetition, setSelectedCompetition] = useState<string>('');
  const [orderBy, setOrderBy] = useState<OrderBy>('name');
  const [order, setOrder] = useState<Order>('asc');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  const { data: teams, isLoading: loadingTeams } = useQuery({
    queryKey: ['teams', selectedCompetition],
    queryFn: () => getTeams(selectedCompetition),
  });

  const { data: competitions } = useQuery({
    queryKey: ['competitions'],
    queryFn: getCompetitions,
  });

  const handleRequestSort = (property: OrderBy) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const getFormColor = (result: string) => {
    switch (result) {
      case 'W': return 'success';
      case 'D': return 'warning';
      case 'L': return 'error';
      default: return 'default';
    }
  };

  // Filter and sort teams
  const filteredTeams = teams?.filter((team: TeamWithStats) =>
    team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    team.stadium?.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const sortedTeams = [...filteredTeams].sort((a, b) => {
    let aValue: any = a[orderBy as keyof TeamWithStats];
    let bValue: any = b[orderBy as keyof TeamWithStats];

    if (orderBy === 'goal_difference') {
      aValue = (a.goals_for || 0) - (a.goals_against || 0);
      bValue = (b.goals_for || 0) - (b.goals_against || 0);
    }

    if (aValue === undefined || aValue === null) aValue = 0;
    if (bValue === undefined || bValue === null) bValue = 0;

    if (order === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  if (loadingTeams) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Teams
      </Typography>

      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search teams..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
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
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={orderBy}
                onChange={(e) => setOrderBy(e.target.value as OrderBy)}
                label="Sort By"
              >
                <MenuItem value="name">Name</MenuItem>
                <MenuItem value="points">Points</MenuItem>
                <MenuItem value="wins">Wins</MenuItem>
                <MenuItem value="goals_for">Goals Scored</MenuItem>
                <MenuItem value="goal_difference">Goal Difference</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>View</InputLabel>
              <Select
                value={viewMode}
                onChange={(e) => setViewMode(e.target.value as 'grid' | 'table')}
                label="View"
              >
                <MenuItem value="grid">Grid View</MenuItem>
                <MenuItem value="table">Table View</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Teams Display */}
      {sortedTeams.length > 0 ? (
        viewMode === 'grid' ? (
          <Grid container spacing={3}>
            {sortedTeams.map((team) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={team.id}>
                <Card>
                  <CardActionArea onClick={() => navigate(`/teams/${team.id}`)}>
                    <CardContent>
                      <Box display="flex" alignItems="center" mb={2}>
                        <Avatar
                          src={team.logo_url}
                          sx={{ width: 60, height: 60, mr: 2 }}
                        >
                          <SportsSoccer />
                        </Avatar>
                        <Box flex={1}>
                          <Typography variant="h6" noWrap>
                            {team.name}
                          </Typography>
                          {team.code && (
                            <Typography variant="body2" color="text.secondary">
                              {team.code}
                            </Typography>
                          )}
                        </Box>
                      </Box>

                      <Box mb={1}>
                        {team.stadium && (
                          <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
                            <Stadium fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary" noWrap>
                              {team.stadium}
                            </Typography>
                          </Box>
                        )}
                        {team.founded && (
                          <Typography variant="body2" color="text.secondary">
                            Founded: {team.founded}
                          </Typography>
                        )}
                      </Box>

                      {team.matches_played !== undefined && team.matches_played > 0 && (
                        <>
                          <Box display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">
                              Matches: {team.matches_played}
                            </Typography>
                            <Typography variant="body2">
                              Points: <strong>{team.points || 0}</strong>
                            </Typography>
                          </Box>
                          
                          <Box display="flex" gap={0.5} mb={1}>
                            <Chip
                              label={`W: ${team.wins || 0}`}
                              size="small"
                              color="success"
                              variant="outlined"
                            />
                            <Chip
                              label={`D: ${team.draws || 0}`}
                              size="small"
                              color="warning"
                              variant="outlined"
                            />
                            <Chip
                              label={`L: ${team.losses || 0}`}
                              size="small"
                              color="error"
                              variant="outlined"
                            />
                          </Box>

                          {team.form && team.form !== 'N/A' && (
                            <Box>
                              <Typography variant="caption" color="text.secondary" gutterBottom>
                                Recent Form
                              </Typography>
                              <Box display="flex" gap={0.5}>
                                {team.form.split('').slice(0, 5).map((result, idx) => (
                                  <Chip
                                    key={idx}
                                    label={result}
                                    size="small"
                                    color={getFormColor(result)}
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </>
                      )}
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Team</TableCell>
                  <TableCell>Stadium</TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={orderBy === 'points'}
                      direction={orderBy === 'points' ? order : 'asc'}
                      onClick={() => handleRequestSort('points')}
                    >
                      Points
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">Played</TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={orderBy === 'wins'}
                      direction={orderBy === 'wins' ? order : 'asc'}
                      onClick={() => handleRequestSort('wins')}
                    >
                      W
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">D</TableCell>
                  <TableCell align="center">L</TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={orderBy === 'goals_for'}
                      direction={orderBy === 'goals_for' ? order : 'asc'}
                      onClick={() => handleRequestSort('goals_for')}
                    >
                      GF
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">GA</TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={orderBy === 'goal_difference'}
                      direction={orderBy === 'goal_difference' ? order : 'asc'}
                      onClick={() => handleRequestSort('goal_difference')}
                    >
                      GD
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Form</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedTeams.map((team) => (
                  <TableRow
                    key={team.id}
                    hover
                    onClick={() => navigate(`/teams/${team.id}`)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Avatar src={team.logo_url} sx={{ width: 30, height: 30 }}>
                          <SportsSoccer fontSize="small" />
                        </Avatar>
                        <Typography variant="body2">{team.name}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{team.stadium || '-'}</TableCell>
                    <TableCell align="center">
                      <strong>{team.points || 0}</strong>
                    </TableCell>
                    <TableCell align="center">{team.matches_played || 0}</TableCell>
                    <TableCell align="center">{team.wins || 0}</TableCell>
                    <TableCell align="center">{team.draws || 0}</TableCell>
                    <TableCell align="center">{team.losses || 0}</TableCell>
                    <TableCell align="center">{team.goals_for || 0}</TableCell>
                    <TableCell align="center">{team.goals_against || 0}</TableCell>
                    <TableCell align="center">
                      {((team.goals_for || 0) - (team.goals_against || 0))}
                    </TableCell>
                    <TableCell>
                      {team.form && team.form !== 'N/A' ? (
                        <Box display="flex" gap={0.25}>
                          {team.form.split('').slice(0, 5).map((result, idx) => (
                            <Chip
                              key={idx}
                              label={result}
                              size="small"
                              color={getFormColor(result)}
                              sx={{ height: 20, minWidth: 20 }}
                            />
                          ))}
                        </Box>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )
      ) : (
        <Alert severity="info">
          {searchTerm ? 'No teams found matching your search criteria' : 'No teams available'}
        </Alert>
      )}
    </Box>
  );
};

export default Teams;