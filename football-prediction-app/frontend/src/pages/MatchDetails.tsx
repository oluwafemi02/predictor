import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';

const MatchDetails: React.FC = () => {
  const { matchId } = useParams();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Match Details
      </Typography>
      <Typography>Match ID: {matchId}</Typography>
      <Typography color="text.secondary">
        Detailed match information and prediction analysis will be displayed here.
      </Typography>
    </Box>
  );
};

export default MatchDetails;