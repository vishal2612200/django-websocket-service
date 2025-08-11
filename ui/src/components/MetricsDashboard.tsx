import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Tooltip,
  Card,
  CardContent,
} from '@mui/material';
import {
  Speed,
  Hub,
  Message,
  TrendingUp,
} from '@mui/icons-material';

interface MetricsData {
  [key: string]: number;
}

interface MetricsDashboardProps {
  metrics: MetricsData;
  derived: {
    avgMsgsPerConn: number;
  };
  onRefresh?: () => void;
}

interface MetricCardProps {
  title: string;
  value: number;
  description: string;
  icon: React.ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
}

function MetricCard({ title, value, description, icon, color = 'primary' }: MetricCardProps) {
  const formatValue = (val: number) => {
    if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
    return val.toLocaleString();
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid',
        borderColor: 'divider',
        '&:hover': {
          borderColor: `${color}.main`,
          boxShadow: 1,
        }
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box display="flex" alignItems="center" gap={1} mb={1}>
          <Box 
            sx={{ 
              color: `${color}.main`,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            {icon}
          </Box>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>
            {title}
          </Typography>
        </Box>
        
        <Typography variant="h4" fontWeight={700} sx={{ mb: 0.5 }}>
          {formatValue(value)}
        </Typography>
        
        <Tooltip title={description} placement="top">
          <Typography variant="caption" color="text.secondary" sx={{ cursor: 'help' }}>
            {description}
          </Typography>
        </Tooltip>
      </CardContent>
    </Card>
  );
}

export default function MetricsDashboard({ 
  metrics, 
  derived, 
  onRefresh
}: MetricsDashboardProps) {
  const activeConnections = metrics['app_active_connections'] ?? 0;
  const totalMessages = metrics['app_messages_total'] ?? 0;
  const sentMessages = metrics['app_messages_sent'] ?? 0;
  const connectionsOpened = metrics['app_connections_opened_total'] ?? 0;

  const metricCards = [
    {
      title: 'Total Connections',
      value: connectionsOpened,
      description: 'Total connections opened since server restart',
      icon: <Hub sx={{ fontSize: 20 }} />,
      color: 'primary' as const,
    },
    {
      title: 'Active Connections',
      value: activeConnections,
      description: 'Current number of active WebSocket connections',
      icon: <TrendingUp sx={{ fontSize: 20 }} />,
      color: 'success' as const,
    },
    {
      title: 'Messages Sent',
      value: sentMessages,
      description: 'Total messages sent by server to clients',
      icon: <Message sx={{ fontSize: 20 }} />,
      color: 'info' as const,
    },
    {
      title: 'Messages Received',
      value: totalMessages,
      description: 'Total messages received from clients',
      icon: <Message sx={{ fontSize: 20 }} />,
      color: 'secondary' as const,
    },
  ];

  return (
    <Paper 
      variant="outlined" 
      sx={{ 
        p: 3, 
        mb: 3,
        borderRadius: 2,
        borderColor: 'divider',
        background: 'rgba(255, 255, 255, 0.02)',
      }}
    >
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Box
          sx={{
            p: 1,
            borderRadius: 2,
            bgcolor: 'primary.main',
            color: 'primary.contrastText',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Speed sx={{ fontSize: 24 }} />
        </Box>
        <Box>
          <Typography variant="h6" fontWeight={600} sx={{ color: 'text.primary', mb: 0.5 }}>
            WebSocket Metrics
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
            Real-time connection and message statistics
          </Typography>
        </Box>
      </Box>

      {/* Metrics Grid */}
      <Grid container spacing={2}>
        {metricCards.map((card, index) => (
          <Grid item xs={12} sm={6} key={index}>
            <MetricCard {...card} />
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
}
