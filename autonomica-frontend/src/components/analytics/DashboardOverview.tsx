import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  Article as ArticleIcon,
  Publish as PublishIcon,
  Share as ShareIcon,
  Public as PublicIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';

interface OverviewData {
  total_content: number;
  published_content: number;
  total_social_posts: number;
  active_platforms: number;
}

interface OverviewCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ReactNode;
  color: string;
  progress?: number;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
}

const OverviewCard: React.FC<OverviewCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color,
  progress,
  trend,
  trendValue
}) => {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUpIcon sx={{ color: 'success.main', fontSize: 16 }} />;
    if (trend === 'down') return <TrendingDownIcon sx={{ color: 'error.main', fontSize: 16 }} />;
    return null;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'success.main';
    if (trend === 'down') return 'error.main';
    return 'text.secondary';
  };

  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              backgroundColor: `${color}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: color
            }}
          >
            {icon}
          </Box>
          
          {trend && (
            <Box display="flex" alignItems="center" gap={0.5}>
              {getTrendIcon()}
              <Typography
                variant="caption"
                color={getTrendColor()}
                fontWeight="medium"
              >
                {trendValue}
              </Typography>
            </Box>
          )}
        </Box>
        
        <Typography variant="h4" component="div" fontWeight="bold" mb={1}>
          {value.toLocaleString()}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" mb={2}>
          {subtitle}
        </Typography>
        
        {progress !== undefined && (
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="caption" color="text.secondary">
                Progress
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {Math.round(progress)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: `${color}20`,
                '& .MuiLinearProgress-bar': {
                  backgroundColor: color,
                  borderRadius: 3
                }
              }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

interface DashboardOverviewProps {
  data: OverviewData;
}

const DashboardOverview: React.FC<DashboardOverviewProps> = ({ data }) => {
  // Calculate derived metrics
  const publishRate = data.total_content > 0 ? (data.published_content / data.total_content) * 100 : 0;
  const postsPerContent = data.published_content > 0 ? data.total_social_posts / data.published_content : 0;
  
  // Mock trend data (in real app, this would come from historical data)
  const mockTrends = {
    total_content: { trend: 'up' as const, value: '+12%' },
    published_content: { trend: 'up' as const, value: '+8%' },
    total_social_posts: { trend: 'up' as const, value: '+15%' },
    active_platforms: { trend: 'stable' as const, value: '0%' }
  };

  return (
    <Grid container spacing={3}>
      {/* Total Content */}
      <Grid item xs={12} sm={6} md={3}>
        <OverviewCard
          title="Total Content"
          value={data.total_content}
          subtitle="All content pieces created"
          icon={<ArticleIcon />}
          color="#1976d2"
          progress={100}
          trend={mockTrends.total_content.trend}
          trendValue={mockTrends.total_content.value}
        />
      </Grid>

      {/* Published Content */}
      <Grid item xs={12} sm={6} md={3}>
        <OverviewCard
          title="Published Content"
          value={data.published_content}
          subtitle="Content ready for social media"
          icon={<PublishIcon />}
          color="#2e7d32"
          progress={publishRate}
          trend={mockTrends.published_content.trend}
          trendValue={mockTrends.published_content.value}
        />
      </Grid>

      {/* Total Social Posts */}
      <Grid item xs={12} sm={6} md={3}>
        <OverviewCard
          title="Social Posts"
          value={data.total_social_posts}
          subtitle="Posts across all platforms"
          icon={<ShareIcon />}
          color="#ed6c02"
          progress={data.total_social_posts > 0 ? Math.min((data.total_social_posts / (data.published_content * 4)) * 100, 100) : 0}
          trend={mockTrends.total_social_posts.trend}
          trendValue={mockTrends.total_social_posts.value}
        />
      </Grid>

      {/* Active Platforms */}
      <Grid item xs={12} sm={6} md={3}>
        <OverviewCard
          title="Active Platforms"
          value={data.active_platforms}
          subtitle="Social media platforms in use"
          icon={<PublicIcon />}
          color="#9c27b0"
          progress={(data.active_platforms / 4) * 100}
          trend={mockTrends.active_platforms.trend}
          trendValue={mockTrends.active_platforms.value}
        />
      </Grid>

      {/* Additional Metrics Row */}
      <Grid item xs={12}>
        <Box
          sx={{
            p: 3,
            backgroundColor: 'background.paper',
            borderRadius: 2,
            border: 1,
            borderColor: 'divider'
          }}
        >
          <Typography variant="h6" gutterBottom>
            Key Performance Indicators
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {publishRate.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Content Publish Rate
                </Typography>
                <Chip
                  label={publishRate > 80 ? 'Excellent' : publishRate > 60 ? 'Good' : 'Needs Improvement'}
                  color={publishRate > 80 ? 'success' : publishRate > 60 ? 'warning' : 'error'}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {postsPerContent.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Posts per Content
                </Typography>
                <Chip
                  label={postsPerContent > 3 ? 'High Coverage' : postsPerContent > 2 ? 'Good Coverage' : 'Low Coverage'}
                  color={postsPerContent > 3 ? 'success' : postsPerContent > 2 ? 'warning' : 'error'}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {data.active_platforms}/4
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Platform Utilization
                </Typography>
                <Chip
                  label={data.active_platforms === 4 ? 'Full Coverage' : `${data.active_platforms}/4 Platforms`}
                  color={data.active_platforms === 4 ? 'success' : 'warning'}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box textAlign="center">
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {data.total_content > 0 ? Math.round((data.published_content / data.total_content) * 100) : 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Content Readiness
                </Typography>
                <Chip
                  label={publishRate > 80 ? 'Ready' : publishRate > 60 ? 'In Progress' : 'Needs Work'}
                  color={publishRate > 80 ? 'success' : publishRate > 60 ? 'warning' : 'error'}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Grid>
    </Grid>
  );
};

export default DashboardOverview;




