import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  ExpandMore as ExpandMoreIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  LineChart as LineChartIcon
} from '@mui/icons-material';
import { analyticsApi } from '../../services/analyticsApi';

interface ContentAnalyticsProps {
  period: string;
  platforms: string[];
  onRefresh: () => void;
}

interface ContentAnalyticsData {
  content_id: number;
  report_period: string;
  generated_at: string;
  overall_score: number;
  platform_performance: Record<string, any>;
  insights: Array<{
    id: string;
    insight_type: string;
    metric_category: string;
    title: string;
    description: string;
    value: number | string;
    confidence: number;
    timestamp: string;
  }>;
  recommendations: string[];
  metrics_summary: {
    total_posts: number;
    platforms: string[];
    analysis_period: {
      start: string;
      end: string;
      days: number;
    };
  };
}

const ContentAnalytics: React.FC<ContentAnalyticsProps> = ({
  period,
  platforms,
  onRefresh
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedContent, setSelectedContent] = useState<ContentAnalyticsData | null>(null);
  const [contentList, setContentList] = useState<ContentAnalyticsData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  // Mock content data for demonstration
  const mockContentData: ContentAnalyticsData[] = [
    {
      content_id: 1,
      report_period: "7d",
      generated_at: new Date().toISOString(),
      overall_score: 85.5,
      platform_performance: {
        twitter: {
          post_id: 101,
          platform_post_id: "tw_123456",
          publish_date: new Date(Date.now() - 86400000).toISOString(),
          last_collected: new Date().toISOString(),
          raw_metrics: {
            like_count: 1250,
            comment_count: 89,
            share_count: 234,
            impression_count: 15000,
            reach_count: 8500
          },
          performance_indicators: {
            engagement_rate: 8.33,
            reach_efficiency: 56.67,
            performance_score: 87.5
          },
          data_quality: {
            score: 92.5,
            grade: "A",
            issues: []
          }
        },
        facebook: {
          post_id: 102,
          platform_post_id: "fb_789012",
          publish_date: new Date(Date.now() - 172800000).toISOString(),
          last_collected: new Date().toISOString(),
          raw_metrics: {
            like_count: 890,
            comment_count: 67,
            share_count: 156,
            impression_count: 12000,
            reach_count: 7200
          },
          performance_indicators: {
            engagement_rate: 7.42,
            reach_efficiency: 60.0,
            performance_score: 82.3
          },
          data_quality: {
            score: 88.0,
            grade: "B",
            issues: ["Data is more than 6 hours old"]
          }
        }
      },
      insights: [
        {
          id: "insight_1",
          insight_type: "performance",
          metric_category: "engagement",
          title: "High Engagement on Twitter",
          description: "Content achieved an above-average engagement rate of 8.33%",
          value: 8.33,
          confidence: 0.85,
          timestamp: new Date().toISOString()
        },
        {
          id: "insight_2",
          insight_type: "engagement",
          metric_category: "engagement",
          title: "Best Engagement on Twitter",
          description: "Twitter achieved the highest engagement rate at 8.33%",
          value: 8.33,
          confidence: 0.85,
          timestamp: new Date().toISOString()
        }
      ],
      recommendations: [
        "Study successful strategies from Twitter and apply them to Facebook",
        "Improve data collection frequency for Facebook to get more accurate insights"
      ],
      metrics_summary: {
        total_posts: 2,
        platforms: ["twitter", "facebook"],
        analysis_period: {
          start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          end: new Date().toISOString(),
          days: 7
        }
      }
    },
    {
      content_id: 2,
      report_period: "7d",
      generated_at: new Date().toISOString(),
      overall_score: 72.8,
      platform_performance: {
        linkedin: {
          post_id: 103,
          platform_post_id: "li_345678",
          publish_date: new Date(Date.now() - 259200000).toISOString(),
          last_collected: new Date().toISOString(),
          raw_metrics: {
            like_count: 456,
            comment_count: 34,
            share_count: 78,
            impression_count: 8000,
            reach_count: 4800
          },
          performance_indicators: {
            engagement_rate: 7.1,
            reach_efficiency: 60.0,
            performance_score: 72.8
          },
          data_quality: {
            score: 85.0,
            grade: "B",
            issues: ["Data is more than 24 hours old"]
          }
        }
      },
      insights: [
        {
          id: "insight_3",
          insight_type: "optimization",
          metric_category: "engagement",
          title: "Improve Data Quality on LinkedIn",
          description: "Data quality score of 85.0 indicates room for improvement",
          value: 85.0,
          confidence: 0.80,
          timestamp: new Date().toISOString()
        }
      ],
      recommendations: [
        "Improve data collection frequency for LinkedIn to get more accurate insights",
        "Content performance is moderate. Focus on improving engagement and reach"
      ],
      metrics_summary: {
        total_posts: 1,
        platforms: ["linkedin"],
        analysis_period: {
          start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          end: new Date().toISOString(),
          days: 7
        }
      }
    }
  ];

  useEffect(() => {
    // Filter content based on platforms if specified
    if (platforms.length > 0) {
      const filtered = mockContentData.filter(content => 
        content.metrics_summary.platforms.some(platform => 
          platforms.includes(platform)
        )
      );
      setContentList(filtered);
    } else {
      setContentList(mockContentData);
    }
  }, [platforms]);

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleViewDetails = (content: ContentAnalyticsData) => {
    setSelectedContent(content);
    setDetailDialogOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailDialogOpen(false);
    setSelectedContent(null);
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

  const filteredContent = contentList.filter(content =>
    content.content_id.toString().includes(searchTerm) ||
    content.metrics_summary.platforms.some(platform => 
      platform.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Content Analytics
        </Typography>
        
        <Box display="flex" gap={2}>
          <TextField
            size="small"
            placeholder="Search content..."
            value={searchTerm}
            onChange={handleSearch}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 250 }}
          />
          
          <Tooltip title="Refresh Data">
            <IconButton onClick={onRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Content Analytics Table */}
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Content ID</TableCell>
              <TableCell>Platforms</TableCell>
              <TableCell>Overall Score</TableCell>
              <TableCell>Posts</TableCell>
              <TableCell>Insights</TableCell>
              <TableCell>Last Updated</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredContent.map((content) => (
              <TableRow key={content.content_id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    #{content.content_id}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Box display="flex" gap={0.5} flexWrap="wrap">
                    {content.metrics_summary.platforms.map((platform) => (
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
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                      variant="body2"
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
                  <Typography variant="body2">
                    {content.metrics_summary.total_posts}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    {content.insights.length} insights
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(content.generated_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleViewDetails(content)}
                      color="primary"
                    >
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary Cards */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Overview
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <Typography variant="h4" color="primary">
                  {contentList.length > 0 
                    ? (contentList.reduce((sum, content) => sum + content.overall_score, 0) / contentList.length).toFixed(1)
                    : '0'
                  }
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Average Score
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={contentList.length > 0 
                  ? (contentList.reduce((sum, content) => sum + content.overall_score, 0) / contentList.length)
                  : 0
                }
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Platform Coverage
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                {['twitter', 'facebook', 'linkedin', 'instagram'].map((platform) => {
                  const count = contentList.filter(content => 
                    content.metrics_summary.platforms.includes(platform)
                  ).length;
                  return (
                    <Box key={platform} display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" textTransform="capitalize">
                        {platform}
                      </Typography>
                      <Chip
                        label={count}
                        size="small"
                        color={count > 0 ? 'primary' : 'default'}
                      />
                    </Box>
                  );
                })}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Insights Summary
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Total Insights</Typography>
                  <Typography variant="h6" color="primary">
                    {contentList.reduce((sum, content) => sum + content.insights.length, 0)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Recommendations</Typography>
                  <Typography variant="h6" color="primary">
                    {contentList.reduce((sum, content) => sum + content.recommendations.length, 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={handleCloseDetails}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Content Analytics Details - #{selectedContent?.content_id}
        </DialogTitle>
        <DialogContent>
          {selectedContent && (
            <Box>
              {/* Overall Performance */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Overall Performance
                  </Typography>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Typography variant="h3" color="primary">
                      {selectedContent.overall_score.toFixed(1)}
                    </Typography>
                    <Box>
                      <Chip
                        label={getScoreLabel(selectedContent.overall_score)}
                        color={getScoreColor(selectedContent.overall_score)}
                        size="medium"
                      />
                      <Typography variant="body2" color="text.secondary" mt={1}>
                        Generated: {new Date(selectedContent.generated_at).toLocaleString()}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              {/* Platform Performance */}
              <Typography variant="h6" gutterBottom>
                Platform Performance
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                {Object.entries(selectedContent.platform_performance).map(([platform, data]) => (
                  <Grid item xs={12} md={6} key={platform}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                          <Typography variant="h6" textTransform="capitalize">
                            {platform}
                          </Typography>
                          <Chip
                            label={`Score: ${data.performance_indicators.performance_score.toFixed(1)}`}
                            color={getScoreColor(data.performance_indicators.performance_score)}
                            size="small"
                          />
                        </Box>
                        
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Engagement Rate
                            </Typography>
                            <Typography variant="h6">
                              {data.performance_indicators.engagement_rate.toFixed(2)}%
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Reach
                            </Typography>
                            <Typography variant="h6">
                              {data.raw_metrics.reach_count.toLocaleString()}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Impressions
                            </Typography>
                            <Typography variant="h6">
                              {data.raw_metrics.impression_count.toLocaleString()}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              Data Quality
                            </Typography>
                            <Chip
                              label={`${data.data_quality.grade} (${data.data_quality.score})`}
                              color={data.data_quality.grade === 'A' ? 'success' : 'warning'}
                              size="small"
                            />
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              {/* Insights */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Insights & Recommendations ({selectedContent.insights.length} insights)
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {selectedContent.insights.map((insight) => (
                      <Grid item xs={12} md={6} key={insight.id}>
                        <Card variant="outlined">
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
                      </Grid>
                    ))}
                  </Grid>
                  
                  <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
                    Recommendations
                  </Typography>
                  <Box>
                    {selectedContent.recommendations.map((recommendation, index) => (
                      <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                        • {recommendation}
                      </Typography>
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
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

export default ContentAnalytics;




