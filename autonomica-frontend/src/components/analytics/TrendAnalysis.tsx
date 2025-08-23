import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Tooltip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Alert,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  Timeline as TimelineIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Download as DownloadIcon,
  CalendarToday as CalendarIcon
} from '@mui/icons-material';
import { analyticsApi } from '../../services/analyticsApi';

interface TrendAnalysisProps {
  period: string;
  platforms: string[];
  onRefresh: () => void;
}

interface TrendData {
  analysis_period: string;
  generated_at: string;
  trend_metrics: {
    engagement_trends: Array<{
      date: string;
      average_engagement_rate: number;
      total_engagement: number;
      content_count: number;
    }>;
    reach_trends: Array<{
      date: string;
      average_reach_efficiency: number;
      total_reach: number;
      content_count: number;
    }>;
    performance_trends: Array<{
      date: string;
      average_performance_score: number;
      top_performing_content: number;
      improvement_rate: number;
    }>;
  };
  platform_trends: Array<{
    platform: string;
    trend_direction: 'increasing' | 'decreasing' | 'stable';
    trend_strength: number; // 0-100
    key_metrics: {
      engagement_change: number;
      reach_change: number;
      performance_change: number;
    };
    insights: Array<{
      id: string;
      trend_type: string;
      title: string;
      description: string;
      impact: 'positive' | 'negative' | 'neutral';
      confidence: number;
    }>;
  }>;
  content_trends: Array<{
    content_id: number;
    content_title: string;
    trend_performance: {
      start_score: number;
      end_score: number;
      improvement: number;
      trend_direction: 'improving' | 'declining' | 'stable';
    };
    platform_performance: Record<string, {
      trend_direction: 'improving' | 'declining' | 'stable';
      improvement_rate: number;
    }>;
  }>;
  seasonal_patterns: Array<{
    pattern_type: string;
    description: string;
    confidence: number;
    recommendations: string[];
  }>;
}

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
      id={`trend-tabpanel-${index}`}
      aria-labelledby={`trend-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `trend-tab-${index}`,
    'aria-controls': `trend-tabpanel-${index}`,
  };
}

const TrendAnalysis: React.FC<TrendAnalysisProps> = ({
  period,
  platforms,
  onRefresh
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedTrend, setSelectedTrend] = useState<any>(null);

  // Mock trend data for demonstration
  const mockTrendData: TrendData = {
    analysis_period: period,
    generated_at: new Date().toISOString(),
    trend_metrics: {
      engagement_trends: [
        { date: '2024-01-01', average_engagement_rate: 6.2, total_engagement: 1250, content_count: 5 },
        { date: '2024-01-02', average_engagement_rate: 6.8, total_engagement: 1380, content_count: 5 },
        { date: '2024-01-03', average_engagement_rate: 7.1, total_engagement: 1420, content_count: 5 },
        { date: '2024-01-04', average_engagement_rate: 7.5, total_engagement: 1500, content_count: 5 },
        { date: '2024-01-05', average_engagement_rate: 7.8, total_engagement: 1560, content_count: 5 },
        { date: '2024-01-06', average_engagement_rate: 8.1, total_engagement: 1620, content_count: 5 },
        { date: '2024-01-07', average_engagement_rate: 8.3, total_engagement: 1660, content_count: 5 }
      ],
      reach_trends: [
        { date: '2024-01-01', average_reach_efficiency: 52.0, total_reach: 8500, content_count: 5 },
        { date: '2024-01-02', average_reach_efficiency: 54.5, total_reach: 8900, content_count: 5 },
        { date: '2024-01-03', average_reach_efficiency: 56.8, total_reach: 9200, content_count: 5 },
        { date: '2024-01-04', average_reach_efficiency: 58.2, total_reach: 9500, content_count: 5 },
        { date: '2024-01-05', average_reach_efficiency: 59.5, total_reach: 9800, content_count: 5 },
        { date: '2024-01-06', average_reach_efficiency: 60.8, total_reach: 10100, content_count: 5 },
        { date: '2024-01-07', average_reach_efficiency: 61.5, total_reach: 10300, content_count: 5 }
      ],
      performance_trends: [
        { date: '2024-01-01', average_performance_score: 72.5, top_performing_content: 1, improvement_rate: 0 },
        { date: '2024-01-02', average_performance_score: 74.2, top_performing_content: 1, improvement_rate: 2.3 },
        { date: '2024-01-03', average_performance_score: 76.8, top_performing_content: 2, improvement_rate: 3.5 },
        { date: '2024-01-04', average_performance_score: 78.5, top_performing_content: 2, improvement_rate: 2.2 },
        { date: '2024-01-05', average_performance_score: 80.1, top_performing_content: 3, improvement_rate: 2.0 },
        { date: '2024-01-06', average_performance_score: 81.8, top_performing_content: 3, improvement_rate: 2.1 },
        { date: '2024-01-07', average_performance_score: 83.2, top_performing_content: 3, improvement_rate: 1.7 }
      ]
    },
    platform_trends: [
      {
        platform: "twitter",
        trend_direction: "increasing",
        trend_strength: 85,
        key_metrics: {
          engagement_change: 12.5,
          reach_change: 8.2,
          performance_change: 15.3
        },
        insights: [
          {
            id: "insight_1",
            trend_type: "performance",
            title: "Strong Growth on Twitter",
            description: "Twitter shows consistent improvement in engagement and reach",
            impact: "positive",
            confidence: 0.90
          }
        ]
      },
      {
        platform: "facebook",
        trend_direction: "stable",
        trend_strength: 45,
        key_metrics: {
          engagement_change: 2.1,
          reach_change: -1.5,
          performance_change: 3.2
        },
        insights: [
          {
            id: "insight_2",
            trend_type: "stability",
            title: "Facebook Performance Stable",
            description: "Facebook maintains consistent performance with minor fluctuations",
            impact: "neutral",
            confidence: 0.75
          }
        ]
      },
      {
        platform: "linkedin",
        trend_direction: "decreasing",
        trend_strength: 65,
        key_metrics: {
          engagement_change: -5.2,
          reach_change: -8.7,
          performance_change: -12.1
        },
        insights: [
          {
            id: "insight_3",
            trend_type: "decline",
            title: "LinkedIn Performance Decline",
            description: "LinkedIn shows declining engagement and reach metrics",
            impact: "negative",
            confidence: 0.80
          }
        ]
      },
      {
        platform: "instagram",
        trend_direction: "increasing",
        trend_strength: 70,
        key_metrics: {
          engagement_change: 8.7,
          reach_change: 6.3,
          performance_change: 9.8
        },
        insights: [
          {
            id: "insight_4",
            trend_type: "growth",
            title: "Instagram Growth Trend",
            description: "Instagram shows positive growth in key metrics",
            impact: "positive",
            confidence: 0.85
          }
        ]
      }
    ],
    content_trends: [
      {
        content_id: 1,
        content_title: "AI Marketing Guide",
        trend_performance: {
          start_score: 75.2,
          end_score: 85.5,
          improvement: 10.3,
          trend_direction: "improving"
        },
        platform_performance: {
          twitter: { trend_direction: "improving", improvement_rate: 12.5 },
          facebook: { trend_direction: "improving", improvement_rate: 8.2 }
        }
      },
      {
        content_id: 2,
        content_title: "Social Media Trends",
        trend_performance: {
          start_score: 78.5,
          end_score: 72.8,
          improvement: -5.7,
          trend_direction: "declining"
        },
        platform_performance: {
          linkedin: { trend_direction: "declining", improvement_rate: -8.7 }
        }
      },
      {
        content_id: 3,
        content_title: "Digital Marketing Tips",
        trend_performance: {
          start_score: 70.1,
          end_score: 78.2,
          improvement: 8.1,
          trend_direction: "improving"
        },
        platform_performance: {
          instagram: { trend_direction: "improving", improvement_rate: 9.8 },
          twitter: { trend_direction: "improving", improvement_rate: 6.3 }
        }
      }
    ],
    seasonal_patterns: [
      {
        pattern_type: "Weekly",
        description: "Performance peaks on Tuesday-Thursday, declines on weekends",
        confidence: 0.85,
        recommendations: [
          "Schedule high-priority content for Tuesday-Thursday",
          "Use weekends for experimental or lower-priority content"
        ]
      },
      {
        pattern_type: "Time-based",
        description: "Best engagement between 9 AM - 2 PM and 6 PM - 8 PM",
        confidence: 0.80,
        recommendations: [
          "Schedule posts during peak engagement hours",
          "Avoid posting during low-engagement periods (3 PM - 5 PM)"
        ]
      }
    ]
  };

  useEffect(() => {
    // Filter data based on selected platforms if specified
    if (platforms.length > 0) {
      const filtered = {
        ...mockTrendData,
        platform_trends: mockTrendData.platform_trends.filter(platform => 
          platforms.includes(platform.platform)
        ),
        content_trends: mockTrendData.content_trends.filter(content => 
          Object.keys(content.platform_performance).some(platform => 
            platforms.includes(platform)
          )
        )
      };
      setTrendData(filtered);
    } else {
      setTrendData(mockTrendData);
    }
  }, [platforms, period]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewDetails = (trend: any) => {
    setSelectedTrend(trend);
    setDetailDialogOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailDialogOpen(false);
    setSelectedTrend(null);
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing':
      case 'improving':
        return <TrendingUpIcon color="success" />;
      case 'decreasing':
      case 'declining':
        return <TrendingDownIcon color="error" />;
      default:
        return <RemoveIcon color="action" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'increasing':
      case 'improving':
        return 'success';
      case 'decreasing':
      case 'declining':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTrendLabel = (direction: string) => {
    switch (direction) {
      case 'increasing':
      case 'improving':
        return 'Improving';
      case 'decreasing':
      case 'declining':
        return 'Declining';
      default:
        return 'Stable';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  if (!trendData) {
    return <Alert severity="info">Loading trend data...</Alert>;
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Trend Analysis
        </Typography>
        
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={onRefresh} color="primary">
              <TimelineIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Trend
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h4" color="success.main">
                  ↗
                </Typography>
                <Box>
                  <Typography variant="h6" color="success.main">
                    +{trendData.trend_metrics.performance_trends[trendData.trend_metrics.performance_trends.length - 1].improvement_rate.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This week
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Engagement Trend
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h4" color="success.main">
                  ↗
                </Typography>
                <Box>
                  <Typography variant="h6" color="success.main">
                    +{((trendData.trend_metrics.engagement_trends[trendData.trend_metrics.engagement_trends.length - 1].average_engagement_rate - trendData.trend_metrics.engagement_trends[0].average_engagement_rate) / trendData.trend_metrics.engagement_trends[0].average_engagement_rate * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This week
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Reach Trend
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h4" color="success.main">
                  ↗
                </Typography>
                <Box>
                  <Typography variant="h6" color="success.main">
                    +{((trendData.trend_metrics.reach_trends[trendData.trend_metrics.reach_trends.length - 1].average_reach_efficiency - trendData.trend_metrics.reach_trends[0].average_reach_efficiency) / trendData.trend_metrics.reach_trends[0].average_reach_efficiency * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    This week
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Platforms
              </Typography>
              <Typography variant="h4" color="primary">
                {trendData.platform_trends.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Platforms analyzed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="trend analysis tabs">
          <Tab label="Platform Trends" {...a11yProps(0)} />
          <Tab label="Content Trends" {...a11yProps(1)} />
          <Tab label="Metric Trends" {...a11yProps(2)} />
          <Tab label="Seasonal Patterns" {...a11yProps(3)} />
        </Tabs>
      </Box>

      {/* Platform Trends Tab */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {trendData.platform_trends.map((platform) => (
            <Grid item xs={12} md={6} key={platform.platform}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" textTransform="capitalize">
                      {platform.platform}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getTrendIcon(platform.trend_direction)}
                      <Chip
                        label={getTrendLabel(platform.trend_direction)}
                        color={getTrendColor(platform.trend_direction)}
                        size="small"
                      />
                    </Box>
                  </Box>
                  
                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Trend Strength: {platform.trend_strength}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={platform.trend_strength}
                      color={getTrendColor(platform.trend_direction)}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  
                  <Grid container spacing={2} mb={2}>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        Engagement
                      </Typography>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        {getTrendIcon(platform.key_metrics.engagement_change > 0 ? 'increasing' : platform.key_metrics.engagement_change < 0 ? 'decreasing' : 'stable')}
                        <Typography variant="h6" color={getTrendColor(platform.key_metrics.engagement_change > 0 ? 'increasing' : platform.key_metrics.engagement_change < 0 ? 'decreasing' : 'stable')}>
                          {platform.key_metrics.engagement_change > 0 ? '+' : ''}{platform.key_metrics.engagement_change.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        Reach
                      </Typography>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        {getTrendIcon(platform.key_metrics.reach_change > 0 ? 'increasing' : platform.key_metrics.reach_change < 0 ? 'decreasing' : 'stable')}
                        <Typography variant="h6" color={getTrendColor(platform.key_metrics.reach_change > 0 ? 'increasing' : platform.key_metrics.reach_change < 0 ? 'decreasing' : 'stable')}>
                          {platform.key_metrics.reach_change > 0 ? '+' : ''}{platform.key_metrics.reach_change.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        Performance
                      </Typography>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        {getTrendIcon(platform.key_metrics.performance_change > 0 ? 'increasing' : platform.key_metrics.performance_change < 0 ? 'decreasing' : 'stable')}
                        <Typography variant="h6" color={getTrendColor(platform.key_metrics.performance_change > 0 ? 'increasing' : platform.key_metrics.performance_change < 0 ? 'decreasing' : 'stable')}>
                          {platform.key_metrics.performance_change > 0 ? '+' : ''}{platform.key_metrics.performance_change.toFixed(1)}%
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                  
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleViewDetails(platform)}
                      color="primary"
                    >
                      <BarChartIcon />
                    </IconButton>
                  </Tooltip>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Content Trends Tab */}
      <TabPanel value={tabValue} index={1}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Content</TableCell>
                <TableCell>Trend Direction</TableCell>
                <TableCell>Improvement</TableCell>
                <TableCell>Platforms</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {trendData.content_trends.map((content) => (
                <TableRow key={content.content_id}>
                  <TableCell>
                    <Typography variant="subtitle1" fontWeight="medium">
                      {content.content_title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ID: #{content.content_id}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      {getTrendIcon(content.trend_performance.trend_direction)}
                      <Chip
                        label={getTrendLabel(content.trend_performance.trend_direction)}
                        color={getTrendColor(content.trend_performance.trend_direction)}
                        size="small"
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Typography
                      variant="body1"
                      color={content.trend_performance.improvement >= 0 ? 'success.main' : 'error.main'}
                      fontWeight="bold"
                    >
                      {content.trend_performance.improvement >= 0 ? '+' : ''}{content.trend_performance.improvement.toFixed(1)} pts
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {content.trend_performance.start_score.toFixed(1)} → {content.trend_performance.end_score.toFixed(1)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {Object.entries(content.platform_performance).map(([platform, data]) => (
                        <Chip
                          key={platform}
                          label={`${platform}: ${data.improvement_rate > 0 ? '+' : ''}${data.improvement_rate.toFixed(1)}%`}
                          size="small"
                          color={getTrendColor(data.trend_direction)}
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(content)}
                        color="primary"
                      >
                        <BarChartIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Metric Trends Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Engagement Rate Trends
                </Typography>
                <Box>
                  {trendData.trend_metrics.engagement_trends.map((trend, index) => (
                    <Box key={trend.date} display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Box display="flex" alignItems="center" gap={2}>
                        <CalendarIcon color="action" fontSize="small" />
                        <Typography variant="body2">
                          {formatDate(trend.date)}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="h6">
                          {trend.average_engagement_rate.toFixed(1)}%
                        </Typography>
                        {index > 0 && (
                          <Chip
                            label={`${trend.average_engagement_rate > trendData.trend_metrics.engagement_trends[index - 1].average_engagement_rate ? '+' : ''}${(trend.average_engagement_rate - trendData.trend_metrics.engagement_trends[index - 1].average_engagement_rate).toFixed(1)}`}
                            size="small"
                            color={trend.average_engagement_rate > trendData.trend_metrics.engagement_trends[index - 1].average_engagement_rate ? 'success' : 'error'}
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Score Trends
                </Typography>
                <Box>
                  {trendData.trend_metrics.performance_trends.map((trend, index) => (
                    <Box key={trend.date} display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Box display="flex" alignItems="center" gap={2}>
                        <CalendarIcon color="action" fontSize="small" />
                        <Typography variant="body2">
                          {formatDate(trend.date)}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="h6">
                          {trend.average_performance_score.toFixed(1)}
                        </Typography>
                        {index > 0 && (
                          <Chip
                            label={`+${trend.improvement_rate.toFixed(1)}%`}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Seasonal Patterns Tab */}
      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          {trendData.seasonal_patterns.map((pattern, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      {pattern.pattern_type} Pattern
                    </Typography>
                    <Chip
                      label={`${Math.round(pattern.confidence * 100)}% confidence`}
                      color="primary"
                      size="small"
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    {pattern.description}
                  </Typography>
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Box>
                    {pattern.recommendations.map((recommendation, recIndex) => (
                      <Typography key={recIndex} variant="body2" sx={{ mb: 1 }}>
                        • {recommendation}
                      </Typography>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={handleCloseDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Trend Details
        </DialogTitle>
        <DialogContent>
          {selectedTrend && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedTrend.platform || selectedTrend.content_title || 'Trend Analysis'}
              </Typography>
              
              {selectedTrend.insights && selectedTrend.insights.length > 0 && (
                <Box mb={3}>
                  <Typography variant="h6" gutterBottom>
                    Key Insights
                  </Typography>
                  {selectedTrend.insights.map((insight: any) => (
                    <Card key={insight.id} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                          {insight.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" mb={2}>
                          {insight.description}
                        </Typography>
                        <Box display="flex" gap={1}>
                          <Chip
                            label={insight.trend_type}
                            size="small"
                            variant="outlined"
                          />
                          <Chip
                            label={insight.impact}
                            color={insight.impact === 'positive' ? 'success' : insight.impact === 'negative' ? 'error' : 'default'}
                            size="small"
                          />
                          <Chip
                            label={`${Math.round(insight.confidence * 100)}% confidence`}
                            size="small"
                            color="primary"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
              
              {selectedTrend.trend_performance && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Performance Trend
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        Start Score
                      </Typography>
                      <Typography variant="h6">
                        {selectedTrend.trend_performance.start_score.toFixed(1)}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        End Score
                      </Typography>
                      <Typography variant="h6">
                        {selectedTrend.trend_performance.end_score.toFixed(1)}
                      </Typography>
                    </Grid>
                    <Grid item xs={4}>
                      <Typography variant="body2" color="text.secondary">
                        Improvement
                      </Typography>
                      <Typography variant="h6" color={selectedTrend.trend_performance.improvement >= 0 ? 'success.main' : 'error.main'}>
                        {selectedTrend.trend_performance.improvement >= 0 ? '+' : ''}{selectedTrend.trend_performance.improvement.toFixed(1)}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDetails}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TrendAnalysis;




