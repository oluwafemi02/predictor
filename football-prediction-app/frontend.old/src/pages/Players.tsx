import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TablePagination,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  LinearProgress,
} from '@mui/material';
import {
  Search,
  Person,
  LocalHospital,
  TrendingUp,
  SportsSoccer,
  Flag,
  Height,
  CalendarToday,
  Info,
} from '@mui/icons-material';
import api from '../services/api';

interface Player {
  id: number;
  name: string;
  position: string;
  team: {
    id: number;
    name: string;
    logo_url: string;
  };
  number?: number;
  age?: number;
  nationality?: string;
  height?: string;
  injured?: boolean;
  stats?: {
    appearances: number;
    goals: number;
    assists: number;
    yellow_cards: number;
    red_cards: number;
    minutes_played: number;
  };
}

interface PlayerDetails {
  player: Player;
  performance: {
    season: string;
    competitions: {
      name: string;
      appearances: number;
      goals: number;
      assists: number;
      minutes: number;
    }[];
  };
  injury_history?: {
    date: string;
    injury: string;
    days_out: number;
  }[];
}

const Players: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState<string>('');
  const [teamFilter, setTeamFilter] = useState<string>('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch all players
  const { data: playersData, isLoading } = useQuery({
    queryKey: ['allPlayers', page, rowsPerPage],
    queryFn: async () => {
      const response = await api.get('/players', {
        params: {
          page: page + 1,
          per_page: rowsPerPage,
        },
      });
      return response.data;
    },
  });

  // Fetch teams for filter
  const { data: teamsData } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const response = await api.get('/teams');
      return response.data;
    },
  });

  // Fetch player details
  const { data: playerDetails, isLoading: loadingDetails } = useQuery({
    queryKey: ['playerDetails', selectedPlayer],
    queryFn: async () => {
      if (!selectedPlayer) return null;
      const response = await api.get(`/players/${selectedPlayer}`);
      return response.data as PlayerDetails;
    },
    enabled: !!selectedPlayer && detailsOpen,
  });

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handlePlayerClick = (playerId: number) => {
    setSelectedPlayer(playerId);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedPlayer(null);
  };

  // Filter players
  const filteredPlayers = playersData?.players?.filter((player: Player) => {
    const matchesSearch = player.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesPosition = !positionFilter || player.position === positionFilter;
    const matchesTeam = !teamFilter || player.team.id.toString() === teamFilter;
    return matchesSearch && matchesPosition && matchesTeam;
  }) || [];

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Players
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Search players"
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
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Position</InputLabel>
                <Select
                  value={positionFilter}
                  onChange={(e) => setPositionFilter(e.target.value)}
                  label="Position"
                >
                  <MenuItem value="">All Positions</MenuItem>
                  <MenuItem value="Goalkeeper">Goalkeeper</MenuItem>
                  <MenuItem value="Defender">Defender</MenuItem>
                  <MenuItem value="Midfielder">Midfielder</MenuItem>
                  <MenuItem value="Forward">Forward</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Team</InputLabel>
                <Select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  label="Team"
                >
                  <MenuItem value="">All Teams</MenuItem>
                  {teamsData?.data?.teams?.map((team: any) => (
                    <MenuItem key={team.id} value={team.id.toString()}>
                      {team.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Players Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Player</TableCell>
              <TableCell>Team</TableCell>
              <TableCell>Position</TableCell>
              <TableCell align="center">Number</TableCell>
              <TableCell align="center">Age</TableCell>
              <TableCell>Nationality</TableCell>
              <TableCell align="center">Apps</TableCell>
              <TableCell align="center">Goals</TableCell>
              <TableCell align="center">Assists</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPlayers.length > 0 ? (
              filteredPlayers.map((player: Player) => (
                <TableRow key={player.id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Avatar sx={{ width: 32, height: 32 }}>
                        {player.name.split(' ').map(n => n[0]).join('')}
                      </Avatar>
                      <Typography variant="body2">{player.name}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Avatar
                        src={player.team.logo_url}
                        sx={{ width: 24, height: 24 }}
                      />
                      <Typography variant="body2">{player.team.name}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={player.position}
                      size="small"
                      color={
                        player.position === 'Goalkeeper' ? 'warning' :
                        player.position === 'Defender' ? 'info' :
                        player.position === 'Midfielder' ? 'success' :
                        'error'
                      }
                    />
                  </TableCell>
                  <TableCell align="center">{player.number || '-'}</TableCell>
                  <TableCell align="center">{player.age || '-'}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      {player.nationality && <Flag fontSize="small" />}
                      {player.nationality || '-'}
                    </Box>
                  </TableCell>
                  <TableCell align="center">{player.stats?.appearances || 0}</TableCell>
                  <TableCell align="center">{player.stats?.goals || 0}</TableCell>
                  <TableCell align="center">{player.stats?.assists || 0}</TableCell>
                  <TableCell align="center">
                    {player.injured ? (
                      <Chip
                        icon={<LocalHospital />}
                        label="Injured"
                        size="small"
                        color="error"
                      />
                    ) : (
                      <Chip
                        label="Fit"
                        size="small"
                        color="success"
                      />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => handlePlayerClick(player.id)}
                    >
                      <Info />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={11} align="center">
                  <Alert severity="info">No players found</Alert>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50]}
          component="div"
          count={playersData?.pagination?.total || 0}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      {/* Player Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Player Details
        </DialogTitle>
        <DialogContent>
          {loadingDetails ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : playerDetails ? (
            <Box>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Avatar sx={{ width: 80, height: 80 }}>
                      {playerDetails.player.name.split(' ').map(n => n[0]).join('')}
                    </Avatar>
                    <Box>
                      <Typography variant="h5">
                        {playerDetails.player.name}
                      </Typography>
                      <Box display="flex" gap={1} mt={1}>
                        <Chip
                          label={playerDetails.player.position}
                          color="primary"
                        />
                        <Chip
                          icon={<Flag />}
                          label={playerDetails.player.nationality || 'Unknown'}
                          variant="outlined"
                        />
                        {playerDetails.player.height && (
                          <Chip
                            icon={<Height />}
                            label={playerDetails.player.height}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  </Box>
                </Grid>

                {/* Season Performance */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Season Performance
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Competition</TableCell>
                          <TableCell align="center">Apps</TableCell>
                          <TableCell align="center">Goals</TableCell>
                          <TableCell align="center">Assists</TableCell>
                          <TableCell align="center">Minutes</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {playerDetails.performance?.competitions?.map((comp, index) => (
                          <TableRow key={index}>
                            <TableCell>{comp.name}</TableCell>
                            <TableCell align="center">{comp.appearances}</TableCell>
                            <TableCell align="center">{comp.goals}</TableCell>
                            <TableCell align="center">{comp.assists}</TableCell>
                            <TableCell align="center">{comp.minutes}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>

                {/* Injury History */}
                {playerDetails.injury_history && playerDetails.injury_history.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Injury History
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell>Injury</TableCell>
                            <TableCell align="center">Days Out</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {playerDetails.injury_history.map((injury, index) => (
                            <TableRow key={index}>
                              <TableCell>{new Date(injury.date).toLocaleDateString()}</TableCell>
                              <TableCell>{injury.injury}</TableCell>
                              <TableCell align="center">{injury.days_out}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                )}
              </Grid>
            </Box>
          ) : (
            <Alert severity="error">Failed to load player details</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Players;