import React from 'react';
import { Box, Typography, Button, Alert, AlertTitle } from '@mui/material';
import { RefreshOutlined, WifiOffOutlined, ErrorOutlineOutlined } from '@mui/icons-material';

interface ApiErrorProps {
  error: any;
  onRetry?: () => void;
  message?: string;
  fullWidth?: boolean;
}

const ApiError: React.FC<ApiErrorProps> = ({ 
  error, 
  onRetry, 
  message,
  fullWidth = false 
}) => {
  // Determine error type and message
  const getErrorInfo = () => {
    if (!error) {
      return {
        type: 'unknown',
        title: 'Error',
        message: message || 'An unexpected error occurred',
        icon: <ErrorOutlineOutlined />,
        severity: 'error' as const,
      };
    }

    // Network error
    if (error.code === 'ERR_NETWORK' || !navigator.onLine) {
      return {
        type: 'network',
        title: 'Connection Error',
        message: 'Unable to connect to the server. Please check your internet connection.',
        icon: <WifiOffOutlined />,
        severity: 'error' as const,
      };
    }

    // API errors with response
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Rate limiting
      if (status === 429) {
        return {
          type: 'rate_limit',
          title: 'Too Many Requests',
          message: data?.message || 'Please wait a moment before trying again.',
          icon: <ErrorOutlineOutlined />,
          severity: 'warning' as const,
        };
      }

      // Authentication errors
      if (status === 401 || status === 403) {
        return {
          type: 'auth',
          title: 'Authentication Required',
          message: data?.message || 'Please log in to access this content.',
          icon: <ErrorOutlineOutlined />,
          severity: 'error' as const,
        };
      }

      // Not found
      if (status === 404) {
        return {
          type: 'not_found',
          title: 'Not Found',
          message: data?.message || 'The requested resource was not found.',
          icon: <ErrorOutlineOutlined />,
          severity: 'info' as const,
        };
      }

      // Server errors
      if (status >= 500) {
        return {
          type: 'server',
          title: 'Server Error',
          message: 'Our servers are experiencing issues. Please try again later.',
          icon: <ErrorOutlineOutlined />,
          severity: 'error' as const,
        };
      }

      // Other API errors
      return {
        type: 'api',
        title: data?.error || 'API Error',
        message: data?.message || message || 'Failed to load data',
        icon: <ErrorOutlineOutlined />,
        severity: 'error' as const,
      };
    }

    // Default error
    return {
      type: 'unknown',
      title: 'Error',
      message: error.message || message || 'An unexpected error occurred',
      icon: <ErrorOutlineOutlined />,
      severity: 'error' as const,
    };
  };

  const errorInfo = getErrorInfo();

  return (
    <Box
      sx={{
        width: fullWidth ? '100%' : 'auto',
        my: 2,
      }}
    >
      <Alert
        severity={errorInfo.severity}
        icon={errorInfo.icon}
        action={
          onRetry && (
            <Button
              color="inherit"
              size="small"
              startIcon={<RefreshOutlined />}
              onClick={onRetry}
            >
              Retry
            </Button>
          )
        }
      >
        <AlertTitle>{errorInfo.title}</AlertTitle>
        <Typography variant="body2">{errorInfo.message}</Typography>
        
        {/* Show additional details in development */}
        {process.env.NODE_ENV === 'development' && error?.response?.data?.details && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(error.response.data.details, null, 2)}
            </Typography>
          </Box>
        )}
      </Alert>
    </Box>
  );
};

export default ApiError;