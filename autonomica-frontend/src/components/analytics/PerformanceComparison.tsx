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
  Alert
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  Compare as CompareIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { analyticsApi } from '../../services/analyticsApi';

interface PerformanceComparisonProps {
  period: string;
  platforms: string[];
  onRefresh: () => void;
}

interface ComparisonData {
  comparison_type: string;
  comparison_period: string;
  generated_at: string;
  content_comparison: Array<{
    content_id: number;
    content_title: string;
    overall_score: number;
    platform_performance: Record<string, any>;
    performance_indicators: {
      engagement_rate: number;
      reach_efficiency: number;
      performance_score: number;
    };
    insights: Array<{
      id: string;
      insight_type: string;
      title: string;
      description: string;
      value: number;
      confidence: number;
    }>;
  }>;
  platform_comparison: Array<{
    platform: string;
    total_posts: number;
    average_engagement_rate: number;
    average_reach_efficiency: number;
    average_performance_score: number;
    top_performing_content: Array<{
      content_id: number;
      content_title: string;
      performance_score: number;
    }>;
  }>;
  cross_platform_metrics: {
    best_performing_platform: string;
    worst_performing_platform: string;
    platform_performance_gap: number;
    content_performance_variance: number;
  };
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
      id={`comparison-tabpanel-${index}`}
      aria-labelledby={`comparison-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `comparison-tab-${index}`,
    'aria-controls': `comparison-tabpanel-${index}`,
  };
}

const PerformanceComparison: React.FC<PerformanceComparisonProps> = ({
  period,
  platforms,
  onRefresh
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedComparison, setSelectedComparison] = useState<any>(null);

  // Mock comparison data for demonstration
  const mockComparisonData: ComparisonData = {
    comparison_type: "comprehensive",
    comparison_period: period,
    generated_at: new Date().toISOString(),
    content_comparison: [
      {
        content_id: 1,
        content_title: "AI Marketing Guide",
        overall_score: 85.5,
        platform_performance: {
          twitter: { performance_score: 87.5, engagement_rate: 8.33 },
          facebook: { performance_score: 82.3, engagement_rate: 7.42 }
        },
        performance_indicators: {
          engagement_rate: 7.88,
          reach_efficiency: 58.34,
          performance_score: 85.5
        },
        insights: [
          {
            id: "insight_1",
            insight_type: "performance",
            title: "Top Performer",
            description: "This content achieved the highest overall performance score",
            value: 85.5,
            confidence: 0.90
          }
        ]
      },
      {
        content_id: 2,
        content_title: "Social Media Trends",
        overall_score: 72.8,
        platform_performance: {
          linkedin: { performance_score: 72.8, engagement_rate: 7.1 }
        },
        performance_indicators: {
          engagement_rate: 7.1,
          reach_efficiency: 60.0,
          performance_score: 72.8
        },
        insights: [
          {
            id: "insight_2",
            insight_type: "optimization",
            title: "Room for Improvement",
            description: "Content performance is moderate with potential for optimization",
            value: 72.8,
            confidence: 0.85
          }
        ]
      },
      {
        content_id: 3,
        content_title: "Digital Marketing Tips",
        overall_score: 78.2,
        platform_performance: {
          instagram: { performance_score: 78.2, engagement_rate: 6.8 },
          twitter: { performance_score: 75.1, engagement_rate: 6.2 }
        },
        performance_indicators: {
          engagement_rate: 6.5,
          reach_efficiency: 52.5,
          performance_score: 78.2
        },
        insights: [
          {
            id: "insight_3",
            insight_type: "performance",
            title: "Consistent Performance",
            description: "Content shows consistent performance across platforms",
            value: 78.2,
            confidence: 0.80
          }
        ]
      }
    ],
    platform_comparison: [
      {
        platform: "twitter",
        total_posts: 2,
        average_engagement_rate: 7.27,
        average_reach_efficiency: 55.42,
        average_performance_score: 81.3,
        top_performing_content: [
          { content_id: 1, content_title: "AI Marketing Guide", performance_score: 87.5 }
        ]
      },
      {
        platform: "facebook",
        total_posts: 1,
        average_engagement_rate: 7.42,
        average_reach_efficiency: 60.0,
        average_performance_score: 82.3,
        top_performing_content: [
          { content_id: 1, content_title: "AI Marketing Guide", performance_score: 82.3 }
        ]
      },
      {
        platform: "linkedin",
        total_posts: 1,
        average_engagement_rate: 7.1,
        average_reach_efficiency: 60.0,
        average_performance_score: 72.8,
        top_performing_content: [
          { content_id: 2, content_title: "Social Media Trends", performance_score: 72.8 }
        ]
      },
      {
        platform: "instagram",
        total_posts: 1,
        average_engagement_rate: 6.8,
        average_reach_efficiency: 52.5,
        average_performance_score: 78.2,
        top_performing_content: [
          { content_id: 3, content_title: "Digital Marketing Tips", performance_score: 78.2 }
        ]
      }
    ],
    cross_platform_metrics: {
      best_performing_platform: "twitter",
      worst_performing_platform: "linkedin",
      platform_performance_gap: 8.5,
      content_performance_variance: 12.7
    }
  };

  useEffect(() => {
    // Filter data based on selected platforms if specified
    if (platforms.length > 0) {
      const filtered = {
        ...mockComparisonData,
        platform_comparison: mockComparisonData.platform_comparison.filter(platform => 
          platforms.includes(platform.platform)
        ),
        content_comparison: mockComparisonData.content_comparison.filter(content => 
          Object.keys(content.platform_performance).some(platform => 
            platforms.includes(platform)
          )
        )
      };
      setComparisonData(filtered);
    } else {
      setComparisonData(mockComparisonData);
    }
  }, [platforms, period]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewDetails = (comparison: any) => {
    setSelectedComparison(comparison);
    setDetailDialogOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailDialogOpen(false);
    setSelectedComparison(null);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Improvement';
  };

  const getTrendIcon = (value: number, threshold: number = 0) => {
    if (value > threshold) return <TrendingUpIcon color="success" />;
    if (value < threshold) return <TrendingDownIcon color="error" />;
    return <RemoveIcon color="action" />;
  };

  if (!comparisonData) {
    return <Alert severity="info">Loading comparison data...</Alert>;
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Performance Comparison
        </Typography>
        
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={onRefresh} color="primary">
              <CompareIcon />
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
                Best Platform
              </Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="h4" color="success.main" textTransform="capitalize">
                  {comparisonData.cross_platform_metrics.best_performing_platform}
                </Typography>
                <TrendingUpIcon color="success" />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Top performing platform
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Gap
              </Typography>
              <Typography variant="h4" color="warning.main">
                {comparisonData.cross_platform_metrics.platform_performance_gap.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Points between best & worst
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Content Variance
              </Typography>
              <Typography variant="h4" color="info.main">
                {comparisonData.cross_platform_metrics.content_performance_variance.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Performance consistency
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Total Content
              </Typography>
              <Typography variant="h4" color="primary">
                {comparisonData.content_comparison.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Pieces compared
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="comparison tabs">
          <Tab label="Content Comparison" {...a11yProps(0)} />
          <Tab label="Platform Comparison" {...a11yProps(1)} />
          <Tab label="Cross-Platform Analysis" {...a11yProps(2)} />
        </Tabs>
      </Box>

      {/* Content Comparison Tab */}
      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Content</TableCell>
                <TableCell>Overall Score</TableCell>
                <TableCell>Engagement Rate</TableCell>
                <TableCell>Reach Efficiency</TableCell>
                <TableCell>Platforms</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparisonData.content_comparison.map((content) => (
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
                      <Typography
                        variant="body1"
                        fontWeight="bold"
                        color={`${getScoreColor(content.overall_score)}.main`}
                      >
                        {content.overall_score.toFixed(1)}
                      </Typography>
                      <Chip
                        label={getScoreLabel(content.overall_score)}
                        color={getScoreColor(content.overall_score)}
                        size="small"
                      />
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2">
                        {content.performance_indicators.engagement_rate.toFixed(2)}%
                      </Typography>
                      {getTrendIcon(content.performance_indicators.engagement_rate, 7.0)}
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1">
                      <Typography variant="body2">
                        {content.performance_indicators.reach_efficiency.toFixed(1)}%
                      </Typography>
                      {getTrendIcon(content.performance_indicators.reach_efficiency, 55.0)}
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {Object.keys(content.platform_performance).map((platform) => (
                        <Chip
                          key={platform}
                          label={platform.charAt(0).toUpperCase() + platform.slice(1)}
                          size="small"
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

      {/* Platform Comparison Tab */}
      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          {comparisonData.platform_comparison.map((platform) => (
            <Grid item xs={12} md={6} key={platform.platform}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" textTransform="capitalize">
                      {platform.platform}
                    </Typography>
                    <Chip
                      label={`Score: ${platform.average_performance_score.toFixed(1)}`}
                      color={getScoreColor(platform.average_performance_score)}
                      size="small"
                    />
                  </Box>
                  
                  <Grid container spacing={2} mb={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Posts
                      </Typography>
                      <Typography variant="h6">
                        {platform.total_posts}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Engagement
                      </Typography>
                      <Typography variant="h6">
                        {platform.average_engagement_rate.toFixed(2)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Reach Efficiency
                      </Typography>
                      <Typography variant="h6">
                        {platform.average_reach_efficiency.toFixed(1)}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Performance
                      </Typography>
                      <Typography variant="h6">
                        {platform.average_performance_score.toFixed(1)}
                      </Typography>
                    </Grid>
                  </Grid>
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Top Performing Content:
                  </Typography>
                  {platform.top_performing_content.map((content) => (
                    <Box key={content.content_id} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2">
                        {content.content_title}
                      </Typography>
                      <Chip
                        label={content.performance_score.toFixed(1)}
                        size="small"
                        color={getScoreColor(content.performance_score)}
                      />
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Cross-Platform Analysis Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Platform Performance Ranking
                </Typography>
                <Box>
                  {comparisonData.platform_comparison
                    .sort((a, b) => b.average_performance_score - a.average_performance_score)
                    .map((platform, index) => (
                      <Box key={platform.platform} display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Chip
                            label={`#${index + 1}`}
                            color={index === 0 ? 'success' : 'default'}
                            size="small"
                          />
                          <Typography variant="body1" textTransform="capitalize">
                            {platform.platform}
                          </Typography>
                        </Box>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="h6" color="primary">
                            {platform.average_performance_score.toFixed(1)}
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={platform.average_performance_score}
                            sx={{ width: 60, height: 6, borderRadius: 3 }}
                          />
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
                  Performance Insights
                </Typography>
                <Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2">Best Platform</Typography>
                    <Chip
                      label={comparisonData.cross_platform_metrics.best_performing_platform}
                      color="success"
                      size="small"
                    />
                  </Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2">Worst Platform</Typography>
                    <Chip
                      label={comparisonData.cross_platform_metrics.worst_performing_platform}
                      color="error"
                      size="small"
                    />
                  </Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2">Performance Gap</Typography>
                    <Typography variant="h6" color="warning.main">
                      {comparisonData.cross_platform_metrics.platform_performance_gap.toFixed(1)} pts
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Content Variance</Typography>
                    <Typography variant="h6" color="info.main">
                      {comparisonData.cross_platform_metrics.content_performance_variance.toFixed(1)} pts
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
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
          Performance Details
        </DialogTitle>
        <DialogContent>
          {selectedComparison && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedComparison.content_title || 'Platform Performance'}
              </Typography>
              
              {selectedComparison.overall_score && (
                <Box mb={3}>
                  <Typography variant="h4" color="primary" gutterBottom>
                    Overall Score: {selectedComparison.overall_score.toFixed(1)}
                  </Typography>
                  <Chip
                    label={getScoreLabel(selectedComparison.overall_score)}
                    color={getScoreColor(selectedComparison.overall_score)}
                    size="medium"
                  />
                </Box>
              )}
              
              {selectedComparison.performance_indicators && (
                <Grid container spacing={2} mb={3}>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">
                      Engagement Rate
                    </Typography>
                    <Typography variant="h6">
                      {selectedComparison.performance_indicators.engagement_rate.toFixed(2)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">
                      Reach Efficiency
                    </Typography>
                    <Typography variant="h6">
                      {selectedComparison.performance_indicators.reach_efficiency.toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">
                      Performance Score
                    </Typography>
                    <Typography variant="h6">
                      {selectedComparison.performance_indicators.performance_score.toFixed(1)}
                    </Typography>
                  </Grid>
                </Grid>
              )}
              
              {selectedComparison.insights && selectedComparison.insights.length > 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Key Insights
                  </Typography>
                  {selectedComparison.insights.map((insight: any) => (
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
                            label={insight.insight_type}
                            size="small"
                            variant="outlined"
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

export default PerformanceComparison;




