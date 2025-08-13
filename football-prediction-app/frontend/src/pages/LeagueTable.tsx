import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  Chip,
  Grid,
  Card,
  CardContent,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  SportsSoccer,
  TrendingUp,
  TrendingDown,
  Remove,
  EmojiEvents,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { getLeagueTable, getCompetitions } from '../services/api';

interface TeamStanding {
  position: number;
  team: {
    id: number;
    name: string;
    logo_url: string;
  };
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  form: string;
}

const LeagueTable: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [selectedCompetition, setSelectedCompetition] = useState<string>('Premier League');
  const [selectedSeason, setSelectedSeason] = useState<string>('2023/2024');

  const { data: competitions } = useQuery({
    queryKey: ['competitions'],
    queryFn: getCompetitions,
  });

  const { data: tableData, isLoading } = useQuery({
    queryKey: ['leagueTable', selectedCompetition, selectedSeason],
    queryFn: () => getLeagueTable(selectedCompetition, selectedSeason),
  });

  const getPositionColor = (position: number) => {
    if (position <= 4) return theme.palette.success.main;
    if (position === 5 || position === 6) return theme.palette.info.main;
    if (position >= (tableData?.table?.length || 20) - 2) return theme.palette.error.main;
    return theme.palette.text.primary;
  };

  const getPositionIcon = (position: number) => {
    if (position === 1) return <EmojiEvents sx={{ color: '#FFD700', fontSize: 20 }} />;
    if (position === 2) return <EmojiEvents sx={{ color: '#C0C0C0', fontSize: 20 }} />;
    if (position === 3) return <EmojiEvents sx={{ color: '#CD7F32', fontSize: 20 }} />;
    return null;
  };

  const getFormColor = (result: string) => {
    switch (result) {
      case 'W': return 'success';
      case 'D': return 'warning';
      case 'L': return 'error';
      default: return 'default';
    }
  };

  const getFormIcon = (form: string) => {
    const wins = (form.match(/W/g) || []).length;
    const losses = (form.match(/L/g) || []).length;
    
    if (wins >= 4) return <TrendingUp color="success" fontSize="small" />;
    if (losses >= 4) return <TrendingDown color="error" fontSize="small" />;
    return <Remove color="action" fontSize="small" />;
  };

  const getPositionTooltip = (position: number) => {
    if (position <= 4) return 'Champions League qualification';
    if (position === 5) return 'Europa League qualification';
    if (position === 6) return 'Europa Conference League qualification';
    if (position >= (tableData?.table?.length || 20) - 2) return 'Relegation zone';
    return '';
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
        League Table
      </Typography>

      {/* Competition and Season Selection */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Competition</InputLabel>
              <Select
                value={selectedCompetition}
                onChange={(e) => setSelectedCompetition(e.target.value)}
                label="Competition"
              >
                {competitions?.map((comp) => (
                  <MenuItem key={comp} value={comp}>
                    {comp}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth>
              <InputLabel>Season</InputLabel>
              <Select
                value={selectedSeason}
                onChange={(e) => setSelectedSeason(e.target.value)}
                label="Season"
              >
                {tableData?.available_seasons?.map((season: string) => (
                  <MenuItem key={season} value={season}>
                    {season}
                  </MenuItem>
                )) || (
                  <MenuItem value="2023/2024">2023/2024</MenuItem>
                )}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card variant="outlined">
              <CardContent sx={{ py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography variant="body1">
                  {tableData?.last_updated
                    ? new Date(tableData.last_updated).toLocaleString()
                    : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* League Table */}
      {tableData?.table && tableData.table.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell align="center" sx={{ width: 60 }}>Pos</TableCell>
                <TableCell>Team</TableCell>
                <TableCell align="center">P</TableCell>
                <TableCell align="center">W</TableCell>
                <TableCell align="center">D</TableCell>
                <TableCell align="center">L</TableCell>
                <TableCell align="center">GF</TableCell>
                <TableCell align="center">GA</TableCell>
                <TableCell align="center">GD</TableCell>
                <TableCell align="center">Pts</TableCell>
                <TableCell align="center">Form</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tableData.table.map((team: TeamStanding, index: number) => {
                const tooltip = getPositionTooltip(team.position);
                return (
                  <TableRow
                    key={team.team.id}
                    hover
                    onClick={() => navigate(`/teams/${team.team.id}`)}
                    sx={{
                      cursor: 'pointer',
                      borderLeft: `4px solid ${getPositionColor(team.position)}`,
                    }}
                  >
                    <TableCell align="center">
                      <Tooltip title={tooltip} arrow placement="left">
                        <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                          <Typography
                            variant="body2"
                            fontWeight="bold"
                            color={getPositionColor(team.position)}
                          >
                            {team.position}
                          </Typography>
                          {getPositionIcon(team.position)}
                        </Box>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Avatar
                          src={team.team.logo_url}
                          sx={{ width: 30, height: 30 }}
                        >
                          <SportsSoccer fontSize="small" />
                        </Avatar>
                        <Typography variant="body2" fontWeight="medium">
                          {team.team.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">{team.played}</TableCell>
                    <TableCell align="center" sx={{ color: theme.palette.success.main }}>
                      {team.won}
                    </TableCell>
                    <TableCell align="center" sx={{ color: theme.palette.warning.main }}>
                      {team.drawn}
                    </TableCell>
                    <TableCell align="center" sx={{ color: theme.palette.error.main }}>
                      {team.lost}
                    </TableCell>
                    <TableCell align="center">{team.goals_for}</TableCell>
                    <TableCell align="center">{team.goals_against}</TableCell>
                    <TableCell align="center">
                      <Typography
                        variant="body2"
                        color={
                          team.goal_difference > 0
                            ? 'success.main'
                            : team.goal_difference < 0
                            ? 'error.main'
                            : 'text.primary'
                        }
                      >
                        {team.goal_difference > 0 && '+'}{team.goal_difference}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body1" fontWeight="bold">
                        {team.points}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" alignItems="center" gap={0.25}>
                        {team.form ? (
                          <>
                            {team.form.split('').slice(-5).map((result, idx) => (
                              <Chip
                                key={idx}
                                label={result}
                                size="small"
                                color={getFormColor(result)}
                                sx={{ height: 20, minWidth: 20 }}
                              />
                            ))}
                            {getFormIcon(team.form)}
                          </>
                        ) : (
                          '-'
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Alert severity="info">
          No data available for {selectedCompetition} - {selectedSeason}
        </Alert>
      )}

      {/* Legend */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Legend
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  bgcolor: theme.palette.success.main,
                  borderRadius: 1,
                }}
              />
              <Typography variant="body2">Champions League</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  bgcolor: theme.palette.info.main,
                  borderRadius: 1,
                }}
              />
              <Typography variant="body2">Europa League / Conference League</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  bgcolor: theme.palette.error.main,
                  borderRadius: 1,
                }}
              />
              <Typography variant="body2">Relegation</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="text.secondary">
                P: Played | W: Won | D: Drawn | L: Lost
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="text.secondary">
                GF: Goals For | GA: Goals Against | GD: Goal Difference | Pts: Points
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default LeagueTable;