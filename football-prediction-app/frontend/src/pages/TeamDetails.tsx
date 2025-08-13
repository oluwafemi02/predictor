import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  Avatar,
  Chip,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Button,
  Divider,
} from '@mui/material';
import {
  SportsSoccer,
  Stadium,
  EmojiEvents,
  Groups,
  Timeline,
  CalendarToday,
  Flag,
  Height,
  LocalHospital,
} from '@mui/icons-material';
import { getTeamDetails, getTeamPlayers, getTeamMatches, getTeamStatistics } from '../services/api';

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
      id={`team-tabpanel-${index}`}
      aria-labelledby={`team-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TeamDetails: React.FC = () => {
  const { teamId } = useParams();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);

  const { data: teamData, isLoading: loadingTeam } = useQuery({
    queryKey: ['team', teamId],
    queryFn: () => getTeamDetails(Number(teamId)),
    enabled: !!teamId,
  });

  const { data: playersData, isLoading: loadingPlayers } = useQuery({
    queryKey: ['teamPlayers', teamId],
    queryFn: () => getTeamPlayers(Number(teamId)),
    enabled: !!teamId && tabValue === 1,
  });

  const { data: matchesData, isLoading: loadingMatches } = useQuery({
    queryKey: ['teamMatches', teamId],
    queryFn: () => getTeamMatches(Number(teamId)),
    enabled: !!teamId && tabValue === 2,
  });

  const { data: statsData, isLoading: loadingStats } = useQuery({
    queryKey: ['teamStatistics', teamId],
    queryFn: () => getTeamStatistics(Number(teamId)),
    enabled: !!teamId,
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loadingTeam) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!teamData?.team) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <Alert severity="error">Team not found</Alert>
      </Box>
    );
  }

  const { team } = teamData;
  const statistics = statsData?.statistics || {};

  return (
    <Box>
      {/* Team Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item>
              <Avatar
                src={team.logo_url}
                alt={team.name}
                sx={{ width: 120, height: 120 }}
              />
            </Grid>
            <Grid item xs>
              <Typography variant="h4" gutterBottom>
                {team.name}
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip
                  icon={<Stadium />}
                  label={team.stadium || 'Stadium not available'}
                  variant="outlined"
                />
                <Chip
                  icon={<CalendarToday />}
                  label={`Founded: ${team.founded || 'N/A'}`}
                  variant="outlined"
                />
                <Chip
                  icon={<Flag />}
                  label={team.code}
                  color="primary"
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      {statistics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  League Position
                </Typography>
                <Typography variant="h4">
                  {statistics.position || '-'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Points
                </Typography>
                <Typography variant="h4">
                  {statistics.points || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Goals For
                </Typography>
                <Typography variant="h4">
                  {statistics.goals_for || '0'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Form
                </Typography>
                <Box display="flex" gap={0.5}>
                  {(statistics.form || 'NNNNN').split('').map((result, index) => (
                    <Chip
                      key={index}
                      label={result}
                      size="small"
                      color={
                        result === 'W' ? 'success' :
                        result === 'D' ? 'warning' :
                        result === 'L' ? 'error' :
                        'default'
                      }
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Overview" icon={<Timeline />} iconPosition="start" />
            <Tab label="Squad" icon={<Groups />} iconPosition="start" />
            <Tab label="Fixtures" icon={<SportsSoccer />} iconPosition="start" />
          </Tabs>
        </Box>

        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          {loadingStats ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Season Statistics
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Matches Played</TableCell>
                        <TableCell align="right">{statistics.matches_played || 0}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Wins</TableCell>
                        <TableCell align="right">{statistics.wins || 0}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Draws</TableCell>
                        <TableCell align="right">{statistics.draws || 0}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Losses</TableCell>
                        <TableCell align="right">{statistics.losses || 0}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Goals Against</TableCell>
                        <TableCell align="right">{statistics.goals_against || 0}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Goal Difference</TableCell>
                        <TableCell align="right">
                          {(statistics.goals_for || 0) - (statistics.goals_against || 0)}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Clean Sheets</TableCell>
                        <TableCell align="right">{statistics.clean_sheets || 0}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Performance
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Win Rate
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    <LinearProgress
                      variant="determinate"
                      value={statistics.matches_played ? (statistics.wins / statistics.matches_played) * 100 : 0}
                      sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="body2">
                      {statistics.matches_played ? Math.round((statistics.wins / statistics.matches_played) * 100) : 0}%
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Goals per Match
                  </Typography>
                  <Typography variant="h6">
                    {statistics.matches_played ? (statistics.goals_for / statistics.matches_played).toFixed(2) : '0.00'}
                  </Typography>
                </Box>

                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Goals Conceded per Match
                  </Typography>
                  <Typography variant="h6">
                    {statistics.matches_played ? (statistics.goals_against / statistics.matches_played).toFixed(2) : '0.00'}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* Squad Tab */}
        <TabPanel value={tabValue} index={1}>
          {loadingPlayers ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : playersData?.players && playersData.players.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Number</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Position</TableCell>
                    <TableCell>Age</TableCell>
                    <TableCell>Nationality</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {playersData.players.map((player) => (
                    <TableRow key={player.id} hover>
                      <TableCell>{player.number || '-'}</TableCell>
                      <TableCell>
                        <Typography variant="body2">{player.name}</Typography>
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
                      <TableCell>{player.age || '-'}</TableCell>
                      <TableCell>{player.nationality || '-'}</TableCell>
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
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No player data available</Alert>
          )}
        </TabPanel>

        {/* Fixtures Tab */}
        <TabPanel value={tabValue} index={2}>
          {loadingMatches ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : matchesData?.matches && matchesData.matches.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Date</TableCell>
                    <TableCell>Competition</TableCell>
                    <TableCell>Home</TableCell>
                    <TableCell align="center">Score</TableCell>
                    <TableCell>Away</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {matchesData.matches.map((match) => (
                    <TableRow key={match.id} hover>
                      <TableCell>
                        {new Date(match.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{match.competition}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Avatar
                            src={match.home_team.logo_url}
                            sx={{ width: 24, height: 24 }}
                          />
                          <Typography variant="body2">
                            {match.home_team.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        {match.status === 'finished' ? (
                          <Typography variant="body1" fontWeight="bold">
                            {match.home_score} - {match.away_score}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Avatar
                            src={match.away_team.logo_url}
                            sx={{ width: 24, height: 24 }}
                          />
                          <Typography variant="body2">
                            {match.away_team.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={match.status}
                          size="small"
                          color={
                            match.status === 'finished' ? 'default' :
                            match.status === 'in_play' ? 'error' :
                            'primary'
                          }
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="info">No match data available</Alert>
          )}
        </TabPanel>
      </Card>
    </Box>
  );
};

export default TeamDetails;