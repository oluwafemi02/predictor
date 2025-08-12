import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

const TeamDetails: React.FC = () => {
  const { teamId } = useParams();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Team Details
      </Typography>
      <Typography>Team ID: {teamId}</Typography>
      <Typography color="text.secondary">
        Detailed team information, player roster, and performance statistics will be displayed here.
      </Typography>
    </Box>
  );
};

export default TeamDetails;