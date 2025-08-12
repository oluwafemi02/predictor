import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  ModelTraining,
  Analytics,
} from '@mui/icons-material';
import { getModelStatus, trainModel } from '../services/api';

const ModelStatus: React.FC = () => {
  const queryClient = useQueryClient();
  const [trainingProgress, setTrainingProgress] = useState(false);

  const { data: modelStatus, isLoading } = useQuery({
    queryKey: ['modelStatus'],
    queryFn: getModelStatus,
  });

  const trainModelMutation = useMutation({
    mutationFn: trainModel,
    onMutate: () => {
      setTrainingProgress(true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modelStatus'] });
      setTrainingProgress(false);
    },
    onError: () => {
      setTrainingProgress(false);
    },
  });

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
        Model Status & Configuration
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="h6">Training Status</Typography>
              {modelStatus?.is_trained ? (
                <Chip
                  icon={<CheckCircle />}
                  label="Trained"
                  color="success"
                  size="small"
                />
              ) : (
                <Chip
                  icon={<Cancel />}
                  label="Not Trained"
                  color="error"
                  size="small"
                />
              )}
            </Box>
            <Button
              variant="contained"
              color="primary"
              onClick={() => trainModelMutation.mutate()}
              disabled={trainingProgress}
              startIcon={trainingProgress ? <CircularProgress size={20} /> : <ModelTraining />}
            >
              {trainingProgress ? 'Training...' : 'Train Model'}
            </Button>
          </Box>

          {trainingProgress && (
            <Box mb={2}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Training in progress... This may take several minutes.
              </Typography>
              <LinearProgress />
            </Box>
          )}

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Model Version: {modelStatus?.model_version || 'N/A'}
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {trainModelMutation.isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to train model. Please check the server logs for details.
        </Alert>
      )}

      {trainModelMutation.isSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Model trained successfully!
        </Alert>
      )}

      {modelStatus?.features && modelStatus.features.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Analytics sx={{ mr: 1, verticalAlign: 'middle' }} />
              Model Features ({modelStatus.features.length})
            </Typography>
            <Divider sx={{ my: 2 }} />
            <List dense>
              {modelStatus.features.map((feature, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={feature}
                    secondary={`Feature ${index + 1}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      <Box mt={3}>
        <Alert severity="info">
          <Typography variant="subtitle2" gutterBottom>
            About the Prediction Model
          </Typography>
          <Typography variant="body2">
            The football prediction model uses an ensemble of machine learning algorithms including:
          </Typography>
          <ul style={{ marginTop: 8, marginBottom: 8 }}>
            <li>XGBoost</li>
            <li>LightGBM</li>
            <li>Random Forest</li>
            <li>Gradient Boosting</li>
          </ul>
          <Typography variant="body2">
            The model analyzes team performance, head-to-head statistics, recent form, injuries, and various other factors to predict match outcomes.
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default ModelStatus;