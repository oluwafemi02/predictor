import React from 'react';
import { Box, Typography } from '@mui/material';

const LeagueTable: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        League Table
      </Typography>
      <Typography color="text.secondary">
        League standings and team rankings will be displayed here.
      </Typography>
    </Box>
  );
};

export default LeagueTable;