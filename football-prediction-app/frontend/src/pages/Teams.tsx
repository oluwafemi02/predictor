import React from 'react';
import { Box, Typography } from '@mui/material';

const Teams: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Teams
      </Typography>
      <Typography color="text.secondary">
        Team listings with statistics and performance data will be displayed here.
      </Typography>
    </Box>
  );
};

export default Teams;