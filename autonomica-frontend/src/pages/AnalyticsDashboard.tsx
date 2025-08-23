import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Chip,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  BarChart,
  LineChart,
  PieChart,
  TrendingUp,
  TrendingDown,
  Remove,
  Refresh,
  Download,
  FilterList,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Insights as InsightsIcon,
  Compare as CompareIcon
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { analyticsApi } from '../services/analyticsApi';
import DashboardOverview from '../components/analytics/DashboardOverview';
import ContentAnalytics from '../components/analytics/ContentAnalytics';
import PerformanceComparison from '../components/analytics/PerformanceComparison';
import TrendAnalysis from '../components/analytics/TrendAnalysis';
import InsightsPanel from '../components/analytics/InsightsPanel';

interface DashboardData {
  overview: {
    total_content: number;
    published_content: number;
    total_social_posts: number;
    active_platforms: number;
  };
  recent_activity: {
    collection_jobs: Array<{
      id: string;
      content_id: number;
      status: string;
      created_at: string;
      platforms: string[];
    }>;
    insights: Array<{
      id: string;
      content_id: number;
      type: string;
      title: string;
      confidence: number;
      created_at: string;
    }>;
  };
  platform_distribution: Record<string, number>;
  service_status: {
    auto_collection_enabled: boolean;
    background_tasks_running: boolean;
    last_updated: string;
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
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `analytics-tab-${index}`,
    'aria-controls': `analytics-tabpanel-${index}`,
  };
}

const AnalyticsDashboard: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedPeriod, setSelectedPeriod] = useState('7d');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);

  // Available platforms
  const availablePlatforms = ['twitter', 'facebook', 'linkedin', 'instagram'];

  // Available time periods
  const timePeriods = [
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' }
  ];

  useEffect(() => {
    fetchDashboardData();
  }, [refreshKey]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await analyticsApi.getDashboardData();
      
      if (response.success) {
        setDashboardData(response.data);
      } else {
        setError('Failed to fetch dashboard data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handlePeriodChange = (event: any) => {
    setSelectedPeriod(event.target.value);
  };

  const handlePlatformChange = (event: any) => {
    setSelectedPlatforms(event.target.value);
  };

  const handleExportData = async (format: 'json' | 'csv') => {
    try {
      // This would typically export all content analytics
      // For now, we'll show a placeholder
      alert(`Exporting data in ${format.toUpperCase()} format...`);
    } catch (err) {
      setError('Failed to export data');
    }
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="60vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={handleRefresh}>
          Retry
        </Button>
      </Container>
    );
  }

  if (!dashboardData) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="warning">
          No dashboard data available. Please try refreshing the page.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <DashboardIcon sx={{ fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" component="h1">
              Analytics Dashboard
            </Typography>
          </Box>
          
          <Box display="flex" gap={2}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Time Period</InputLabel>
              <Select
                value={selectedPeriod}
                label="Time Period"
                onChange={handlePeriodChange}
              >
                {timePeriods.map((period) => (
                  <MenuItem key={period.value} value={period.value}>
                    {period.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Platforms</InputLabel>
              <Select
                multiple
                value={selectedPlatforms}
                label="Platforms"
                onChange={handlePlatformChange}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {availablePlatforms.map((platform) => (
                  <MenuItem key={platform} value={platform}>
                    {platform.charAt(0).toUpperCase() + platform.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Tooltip title="Refresh Data">
              <IconButton onClick={handleRefresh} color="primary">
                <Refresh />
              </IconButton>
            </Tooltip>
            
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => handleExportData('csv')}
            >
              Export CSV
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => handleExportData('json')}
            >
              Export JSON
            </Button>
          </Box>
        </Box>
        
        {/* Service Status */}
        <Box display="flex" gap={2} alignItems="center">
          <Chip
            label={`Auto Collection: ${dashboardData.service_status.auto_collection_enabled ? 'Enabled' : 'Disabled'}`}
            color={dashboardData.service_status.auto_collection_enabled ? 'success' : 'default'}
            size="small"
          />
          <Chip
            label={`Background Tasks: ${dashboardData.service_status.background_tasks_running ? 'Running' : 'Stopped'}`}
            color={dashboardData.service_status.background_tasks_running ? 'success' : 'warning'}
            size="small"
          />
          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(dashboardData.service_status.last_updated).toLocaleString()}
          </Typography>
        </Box>
      </Box>

      {/* Dashboard Overview Cards */}
      <DashboardOverview data={dashboardData.overview} />

      {/* Main Content Tabs */}
      <Card sx={{ mt: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="analytics dashboard tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <AnalyticsIcon fontSize="small" />
                  Content Analytics
                </Box>
              }
              {...a11yProps(0)}
            />
            <Tab
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <CompareIcon fontSize="small" />
                  Performance Comparison
                </Box>
              }
              {...a11yProps(1)}
            />
            <Tab
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <TrendingUp fontSize="small" />
                  Trend Analysis
                </Box>
              }
              {...a11yProps(2)}
            />
            <Tab
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <InsightsIcon fontSize="small" />
                  Insights & Recommendations
                </Box>
              }
              {...a11yProps(3)}
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <ContentAnalytics
            period={selectedPeriod}
            platforms={selectedPlatforms}
            onRefresh={handleRefresh}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <PerformanceComparison
            period={selectedPeriod}
            platforms={selectedPlatforms}
            onRefresh={handleRefresh}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <TrendAnalysis
            period={selectedPeriod}
            platforms={selectedPlatforms}
            onRefresh={handleRefresh}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <InsightsPanel
            period={selectedPeriod}
            platforms={selectedPlatforms}
            onRefresh={handleRefresh}
          />
        </TabPanel>
      </Card>

      {/* Recent Activity */}
      <Grid container spacing={3} sx={{ mt: 4 }}>
        {/* Recent Collection Jobs */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Collection Jobs
              </Typography>
              {dashboardData.recent_activity.collection_jobs.length > 0 ? (
                <Box>
                  {dashboardData.recent_activity.collection_jobs.map((job) => (
                    <Box
                      key={job.id}
                      sx={{
                        p: 2,
                        mb: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Content ID: {job.content_id}
                        </Typography>
                        <Typography variant="body2">
                          Platforms: {job.platforms.join(', ')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(job.created_at).toLocaleString()}
                        </Typography>
                      </Box>
                      <Chip
                        label={job.status}
                        color={
                          job.status === 'completed' ? 'success' :
                          job.status === 'failed' ? 'error' :
                          job.status === 'collecting' ? 'warning' : 'default'
                        }
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent collection jobs
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Insights */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Insights
              </Typography>
              {dashboardData.recent_activity.insights.length > 0 ? (
                <Box>
                  {dashboardData.recent_activity.insights.map((insight) => (
                    <Box
                      key={insight.id}
                      sx={{
                        p: 2,
                        mb: 2,
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1
                      }}
                    >
                      <Typography variant="body2" fontWeight="medium">
                        {insight.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Content ID: {insight.content_id}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={1}>
                        <Chip
                          label={insight.type}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${Math.round(insight.confidence * 100)}% confidence`}
                          size="small"
                          color="primary"
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                        {new Date(insight.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No recent insights
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AnalyticsDashboard;




