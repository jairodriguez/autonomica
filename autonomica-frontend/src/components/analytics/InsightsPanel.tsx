import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Lightbulb as LightbulbIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Star as StarIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  AutoAwesome as AutoAwesomeIcon,
  Psychology as PsychologyIcon,
  Analytics as AnalyticsIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { analyticsApi } from '../../services/analyticsApi';

interface InsightsPanelProps {
  period: string;
  platforms: string[];
  onRefresh: () => void;
}

interface InsightData {
  generated_at: string;
  analysis_period: string;
  insights: Array<{
    id: string;
    insight_type: 'performance' | 'optimization' | 'trend' | 'opportunity' | 'warning';
    category: 'engagement' | 'reach' | 'content' | 'platform' | 'timing' | 'audience';
    title: string;
    description: string;
    impact: 'high' | 'medium' | 'low';
    confidence: number;
    priority: 'critical' | 'high' | 'medium' | 'low';
    actionable: boolean;
    recommendations: Array<{
      id: string;
      title: string;
      description: string;
      effort: 'low' | 'medium' | 'high';
      expected_impact: 'high' | 'medium' | 'low';
      implementation_steps: string[];
    }>;
    related_metrics: {
      current_value: number;
      benchmark: number;
      improvement_potential: number;
    };
    timestamp: string;
  }>;
  summary: {
    total_insights: number;
    critical_insights: number;
    high_priority_insights: number;
    actionable_insights: number;
    overall_confidence: number;
    improvement_opportunities: number;
  };
  trends: Array<{
    trend_type: string;
    direction: 'positive' | 'negative' | 'neutral';
    strength: number;
    description: string;
    confidence: number;
  }>;
}

const InsightsPanel: React.FC<InsightsPanelProps> = ({
  period,
  platforms,
  onRefresh
}) => {
  const [insightsData, setInsightsData] = useState<InsightData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<any>(null);
  const [expandedInsights, setExpandedInsights] = useState<string[]>([]);

  // Mock insights data for demonstration
  const mockInsightsData: InsightData = {
    generated_at: new Date().toISOString(),
    analysis_period: period,
    insights: [
      {
        id: "insight_1",
        insight_type: "performance",
        category: "engagement",
        title: "Twitter Engagement Outperforming Other Platforms",
        description: "Twitter shows 15.3% higher engagement rates compared to other platforms. This suggests your content resonates better with Twitter's audience and algorithm.",
        impact: "high",
        confidence: 0.92,
        priority: "high",
        actionable: true,
        recommendations: [
          {
            id: "rec_1_1",
            title: "Increase Twitter Content Frequency",
            description: "Leverage Twitter's strong performance by posting more frequently",
            effort: "low",
            expected_impact: "high",
            implementation_steps: [
              "Increase Twitter posts from 3 to 5 per week",
              "Focus on content types that perform well on Twitter",
              "Monitor engagement metrics for optimization"
            ]
          },
          {
            id: "rec_1_2",
            title: "Study Twitter Success Patterns",
            description: "Analyze what makes content successful on Twitter and apply to other platforms",
            effort: "medium",
            expected_impact: "medium",
            implementation_steps: [
              "Review top-performing Twitter posts",
              "Identify common themes and formats",
              "Adapt successful elements for other platforms"
            ]
          }
        ],
        related_metrics: {
          current_value: 8.33,
          benchmark: 6.5,
          improvement_potential: 28.2
        },
        timestamp: new Date().toISOString()
      },
      {
        id: "insight_2",
        insight_type: "optimization",
        category: "content",
        title: "Content Performance Variance Too High",
        description: "Your content shows significant performance variance (12.7 points), indicating inconsistent quality or targeting. This creates unpredictable results.",
        impact: "medium",
        confidence: 0.87,
        priority: "medium",
        actionable: true,
        recommendations: [
          {
            id: "rec_2_1",
            title: "Standardize Content Quality",
            description: "Implement consistent content creation guidelines",
            effort: "medium",
            expected_impact: "high",
            implementation_steps: [
              "Create content quality checklist",
              "Establish review process for all content",
              "Train team on quality standards"
            ]
          }
        ],
        related_metrics: {
          current_value: 12.7,
          benchmark: 8.0,
          improvement_potential: 37.0
        },
        timestamp: new Date().toISOString()
      },
      {
        id: "insight_3",
        insight_type: "trend",
        category: "platform",
        title: "LinkedIn Performance Declining",
        description: "LinkedIn shows consistent decline in engagement (-5.2%) and reach (-8.7%) over the analysis period. This requires immediate attention.",
        impact: "high",
        confidence: 0.89,
        priority: "critical",
        actionable: true,
        recommendations: [
          {
            id: "rec_3_1",
            title: "Audit LinkedIn Strategy",
            description: "Review and revise LinkedIn content strategy",
            effort: "high",
            expected_impact: "high",
            implementation_steps: [
              "Analyze LinkedIn algorithm changes",
              "Review competitor strategies",
              "Test new content formats",
              "Optimize posting times"
            ]
          }
        ],
        related_metrics: {
          current_value: -8.7,
          benchmark: 0.0,
          improvement_potential: 100.0
        },
        timestamp: new Date().toISOString()
      },
      {
        id: "insight_4",
        insight_type: "opportunity",
        category: "timing",
        title: "Peak Engagement Windows Identified",
        description: "Analysis reveals optimal posting times: Tuesday-Thursday 9 AM - 2 PM and 6 PM - 8 PM. Leveraging these windows could improve engagement by 20-30%.",
        impact: "medium",
        confidence: 0.85,
        priority: "medium",
        actionable: true,
        recommendations: [
          {
            id: "rec_4_1",
            title: "Optimize Posting Schedule",
            description: "Schedule high-priority content during peak engagement windows",
            effort: "low",
            expected_impact: "medium",
            implementation_steps: [
              "Update content calendar with optimal times",
              "Prioritize important content for peak windows",
              "Use scheduling tools for consistency"
            ]
          }
        ],
        related_metrics: {
          current_value: 7.2,
          benchmark: 8.5,
          improvement_potential: 18.1
        },
        timestamp: new Date().toISOString()
      },
      {
        id: "insight_5",
        insight_type: "warning",
        category: "data",
        title: "Facebook Data Quality Issues",
        description: "Facebook data shows signs of being outdated (more than 6 hours old), which could lead to inaccurate insights and poor decision-making.",
        impact: "medium",
        confidence: 0.78,
        priority: "high",
        actionable: true,
        recommendations: [
          {
            id: "rec_5_1",
            title: "Improve Data Collection",
            description: "Enhance Facebook data collection frequency and reliability",
            effort: "medium",
            expected_impact: "medium",
            implementation_steps: [
              "Review Facebook API integration",
              "Increase data collection frequency",
              "Implement data quality monitoring",
              "Set up alerts for data issues"
            ]
          }
        ],
        related_metrics: {
          current_value: 88.0,
          benchmark: 95.0,
          improvement_potential: 7.9
        },
        timestamp: new Date().toISOString()
      }
    ],
    summary: {
      total_insights: 5,
      critical_insights: 1,
      high_priority_insights: 2,
      actionable_insights: 5,
      overall_confidence: 0.86,
      improvement_opportunities: 8
    },
    trends: [
      {
        trend_type: "Overall Performance",
        direction: "positive",
        strength: 75,
        description: "Strong upward trend in overall performance scores",
        confidence: 0.88
      },
      {
        trend_type: "Engagement Rates",
        direction: "positive",
        strength: 68,
        description: "Consistent improvement in engagement across platforms",
        confidence: 0.85
      },
      {
        trend_type: "Platform Diversity",
        direction: "neutral",
        strength: 45,
        description: "Performance varies significantly across platforms",
        confidence: 0.82
      }
    ]
  };

  useEffect(() => {
    // Filter insights based on selected platforms if specified
    if (platforms.length > 0) {
      const filtered = {
        ...mockInsightsData,
        insights: mockInsightsData.insights.filter(insight => 
          insight.category === 'platform' || 
          insight.recommendations.some(rec => 
            rec.implementation_steps.some(step => 
              platforms.some(platform => 
                step.toLowerCase().includes(platform.toLowerCase())
              )
            )
          )
        )
      };
      setInsightsData(filtered);
    } else {
      setInsightsData(mockInsightsData);
    }
  }, [platforms, period]);

  const handleViewDetails = (insight: any) => {
    setSelectedInsight(insight);
    setDetailDialogOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailDialogOpen(false);
    setSelectedInsight(null);
  };

  const handleInsightToggle = (insightId: string) => {
    setExpandedInsights(prev => 
      prev.includes(insightId) 
        ? prev.filter(id => id !== insightId)
        : [...prev, insightId]
    );
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <TrendingUpIcon color="success" />;
      case 'optimization':
        return <AutoAwesomeIcon color="primary" />;
      case 'trend':
        return <AnalyticsIcon color="info" />;
      case 'opportunity':
        return <StarIcon color="warning" />;
      case 'warning':
        return <WarningIcon color="error" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'performance':
        return 'success';
      case 'optimization':
        return 'primary';
      case 'trend':
        return 'info';
      case 'opportunity':
        return 'warning';
      case 'warning':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  if (!insightsData) {
    return <Alert severity="info">Loading insights...</Alert>;
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          AI Insights & Recommendations
        </Typography>
        
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh Insights">
            <IconButton onClick={onRefresh} color="primary">
              <RefreshIcon />
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
                Total Insights
              </Typography>
              <Typography variant="h4" color="primary">
                {insightsData.summary.total_insights}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI-generated insights
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Critical Issues
              </Typography>
              <Typography variant="h4" color="error">
                {insightsData.summary.critical_insights}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Require immediate attention
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actionable
              </Typography>
              <Typography variant="h4" color="success">
                {insightsData.summary.actionable_insights}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                With clear next steps
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Confidence
              </Typography>
              <Typography variant="h4" color="info">
                {Math.round(insightsData.summary.overall_confidence * 100)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Overall AI confidence
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trends Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Key Trends
          </Typography>
          <Grid container spacing={2}>
            {insightsData.trends.map((trend, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Box display="flex" alignItems="center" gap={2}>
                  {getInsightIcon(trend.direction === 'positive' ? 'performance' : trend.direction === 'negative' ? 'warning' : 'trend')}
                  <Box>
                    <Typography variant="subtitle1" fontWeight="medium">
                      {trend.trend_type}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {trend.description}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1} mt={1}>
                      <Chip
                        label={trend.direction}
                        color={trend.direction === 'positive' ? 'success' : trend.direction === 'negative' ? 'error' : 'default'}
                        size="small"
                      />
                      <Typography variant="body2" color="text.secondary">
                        {Math.round(trend.confidence * 100)}% confidence
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Insights List */}
      <Typography variant="h6" gutterBottom>
        Detailed Insights
      </Typography>
      
      {insightsData.insights.map((insight) => (
        <Card key={insight.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Box display="flex" alignItems="center" gap={2}>
                {getInsightIcon(insight.insight_type)}
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {insight.title}
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    <Chip
                      label={insight.insight_type}
                      color={getInsightColor(insight.insight_type)}
                      size="small"
                    />
                    <Chip
                      label={insight.category}
                      variant="outlined"
                      size="small"
                    />
                    <Chip
                      label={`Priority: ${insight.priority}`}
                      color={getPriorityColor(insight.priority)}
                      size="small"
                    />
                    <Chip
                      label={`Impact: ${insight.impact}`}
                      color={getImpactColor(insight.impact)}
                      size="small"
                    />
                  </Box>
                </Box>
              </Box>
              
              <Box display="flex" gap={1}>
                <Chip
                  label={`${Math.round(insight.confidence * 100)}%`}
                  color="primary"
                  size="small"
                />
                <Tooltip title="View Details">
                  <IconButton
                    size="small"
                    onClick={() => handleViewDetails(insight)}
                    color="primary"
                  >
                    <PsychologyIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            <Typography variant="body2" color="text.secondary" mb={2}>
              {insight.description}
            </Typography>
            
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Current: {insight.related_metrics.current_value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Benchmark: {insight.related_metrics.benchmark}
                </Typography>
              </Box>
              <Box textAlign="right">
                <Typography variant="body2" color="text.secondary">
                  Improvement Potential
                </Typography>
                <Typography variant="h6" color="success.main">
                  +{insight.related_metrics.improvement_potential.toFixed(1)}%
                </Typography>
              </Box>
            </Box>
            
            <Accordion
              expanded={expandedInsights.includes(insight.id)}
              onChange={() => handleInsightToggle(insight.id)}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle2">
                  Recommendations ({insight.recommendations.length})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {insight.recommendations.map((recommendation) => (
                    <Grid item xs={12} md={6} key={recommendation.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                            <Typography variant="subtitle1" fontWeight="medium">
                              {recommendation.title}
                            </Typography>
                            <Box display="flex" gap={1}>
                              <Chip
                                label={`Effort: ${recommendation.effort}`}
                                color={getEffortColor(recommendation.effort)}
                                size="small"
                              />
                              <Chip
                                label={`Impact: ${recommendation.expected_impact}`}
                                color={getImpactColor(recommendation.expected_impact)}
                                size="small"
                              />
                            </Box>
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" mb={2}>
                            {recommendation.description}
                          </Typography>
                          
                          <Typography variant="subtitle2" gutterBottom>
                            Implementation Steps:
                          </Typography>
                          <List dense>
                            {recommendation.implementation_steps.map((step, index) => (
                              <ListItem key={index} sx={{ py: 0.5 }}>
                                <ListItemIcon sx={{ minWidth: 24 }}>
                                  <CheckCircleIcon fontSize="small" color="primary" />
                                </ListItemIcon>
                                <ListItemText primary={step} />
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          </CardContent>
        </Card>
      ))}

      {/* Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={handleCloseDetails}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            {selectedInsight && getInsightIcon(selectedInsight.insight_type)}
            <Typography variant="h6">
              {selectedInsight?.title}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedInsight && (
            <Box>
              <Box display="flex" gap={1} mb={3} flexWrap="wrap">
                <Chip
                  label={selectedInsight.insight_type}
                  color={getInsightColor(selectedInsight.insight_type)}
                />
                <Chip
                  label={selectedInsight.category}
                  variant="outlined"
                />
                <Chip
                  label={`Priority: ${selectedInsight.priority}`}
                  color={getPriorityColor(selectedInsight.priority)}
                />
                <Chip
                  label={`Impact: ${selectedInsight.impact}`}
                  color={getImpactColor(selectedInsight.impact)}
                />
                <Chip
                  label={`${Math.round(selectedInsight.confidence * 100)}% confidence`}
                  color="primary"
                />
              </Box>
              
              <Typography variant="body1" paragraph>
                {selectedInsight.description}
              </Typography>
              
              <Grid container spacing={3} mb={3}>
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Current Performance
                      </Typography>
                      <Typography variant="h4" color="primary">
                        {selectedInsight.related_metrics.current_value}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Current metric value
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Benchmark
                      </Typography>
                      <Typography variant="h4" color="info">
                        {selectedInsight.related_metrics.benchmark}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Industry standard
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Improvement Potential
                      </Typography>
                      <Typography variant="h4" color="success">
                        +{selectedInsight.related_metrics.improvement_potential.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Potential improvement
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
              
              <Typography variant="h6" gutterBottom>
                Recommendations
              </Typography>
              
              {selectedInsight.recommendations.map((recommendation) => (
                <Card key={recommendation.id} variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6">
                        {recommendation.title}
                      </Typography>
                      <Box display="flex" gap={1}>
                        <Chip
                          label={`Effort: ${recommendation.effort}`}
                          color={getEffortColor(recommendation.effort)}
                          size="small"
                        />
                        <Chip
                          label={`Impact: ${recommendation.expected_impact}`}
                          color={getImpactColor(recommendation.expected_impact)}
                          size="small"
                        />
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      {recommendation.description}
                    </Typography>
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Implementation Steps:
                    </Typography>
                    <List dense>
                      {recommendation.implementation_steps.map((step, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 24 }}>
                            <CheckCircleIcon fontSize="small" color="primary" />
                          </ListItemIcon>
                          <ListItemText primary={step} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              ))}
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

export default InsightsPanel;




