'use client';

import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  PostAdd as PostAddIcon,
  Schedule as ScheduleIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon
} from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { ProtectedRoute, PERMISSIONS } from '../components/auth/ProtectedRoute';
import AnalyticsDashboard from '../pages/AnalyticsDashboard';
import UserManagement from '../components/auth/UserManagement';

const MainPage: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, isAuthenticated, isLoading, hasPermission } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState<'dashboard' | 'analytics' | 'users'>('dashboard');

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleViewChange = (view: 'dashboard' | 'analytics' | 'users') => {
    setCurrentView(view);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'analytics':
        return (
          <ProtectedRoute requiredPermissions={[PERMISSIONS.VIEW_ANALYTICS]}>
            <AnalyticsDashboard />
          </ProtectedRoute>
        );
      case 'users':
        return (
          <ProtectedRoute requiredPermissions={[PERMISSIONS.VIEW_USERS]}>
            <UserManagement />
          </ProtectedRoute>
        );
      default:
        return <DashboardOverview />;
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (!isAuthenticated) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <Typography variant="h4">Please sign in to access the platform</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Autonomica
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Welcome, {user?.first_name || user?.email}
          </Typography>
          <Button color="inherit" startIcon={<LogoutIcon />}>
            Sign Out
          </Button>
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        variant={isMobile ? 'temporary' : 'permanent'}
        open={isMobile ? drawerOpen : true}
        onClose={handleDrawerToggle}
        sx={{
          width: 240,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 240,
            boxSizing: 'border-box',
            marginTop: '64px'
          }
        }}
      >
        <List>
          <ListItem button onClick={() => handleViewChange('dashboard')}>
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItem>
          
          {hasPermission(PERMISSIONS.VIEW_ANALYTICS) && (
            <ListItem button onClick={() => handleViewChange('analytics')}>
              <ListItemIcon>
                <AnalyticsIcon />
              </ListItemIcon>
              <ListItemText primary="Analytics" />
            </ListItem>
          )}
          
          {hasPermission(PERMISSIONS.CREATE_CONTENT) && (
            <ListItem button>
              <ListItemIcon>
                <PostAddIcon />
              </ListItemIcon>
              <ListItemText primary="Create Content" />
            </ListItem>
          )}
          
          {hasPermission(PERMISSIONS.SCHEDULE_POSTS) && (
            <ListItem button>
              <ListItemIcon>
                <ScheduleIcon />
              </ListItemIcon>
              <ListItemText primary="Schedule Posts" />
            </ListItem>
          )}
          
          {hasPermission(PERMISSIONS.VIEW_USERS) && (
            <ListItem button onClick={() => handleViewChange('users')}>
              <ListItemIcon>
                <PeopleIcon />
              </ListItemIcon>
              <ListItemText primary="User Management" />
            </ListItem>
          )}
          
          <Divider />
          
          <ListItem button>
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItem>
        </List>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          marginTop: '64px',
          marginLeft: { xs: 0, md: '240px' }
        }}
      >
        <Container maxWidth="xl">
          {renderCurrentView()}
        </Container>
      </Box>
    </Box>
  );
};

// Dashboard Overview Component
const DashboardOverview: React.FC = () => {
  const { user, hasPermission } = useAuth();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome to Autonomica
      </Typography>
      
      <Grid container spacing={3}>
        {/* Quick Stats */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Your Role
              </Typography>
              <Typography variant="h4">
                {user?.role || 'Unknown'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Account Status
              </Typography>
              <Typography variant="h6" color={user?.is_active ? 'success.main' : 'error.main'}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Verification
              </Typography>
              <Typography variant="h6" color={user?.is_verified ? 'success.main' : 'warning.main'}>
                {user?.is_verified ? 'Verified' : 'Unverified'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Last Login
              </Typography>
              <Typography variant="body2">
                {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Feature Cards */}
        {hasPermission(PERMISSIONS.VIEW_ANALYTICS) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Analytics Dashboard
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  View comprehensive analytics and insights for your social media performance.
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={() => window.location.href = '#analytics'}>
                  View Analytics
                </Button>
              </CardActions>
            </Card>
          </Grid>
        )}
        
        {hasPermission(PERMISSIONS.CREATE_CONTENT) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Content Creation
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Create and manage engaging content for your social media platforms.
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small">Create Content</Button>
              </CardActions>
            </Card>
          </Grid>
        )}
        
        {hasPermission(PERMISSIONS.SCHEDULE_POSTS) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Post Scheduling
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Schedule posts across multiple platforms at optimal times.
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small">Schedule Posts</Button>
              </CardActions>
            </Card>
          </Grid>
        )}
        
        {hasPermission(PERMISSIONS.VIEW_USERS) && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  User Management
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Manage team members, roles, and permissions.
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={() => window.location.href = '#users'}>
                  Manage Users
                </Button>
              </CardActions>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default MainPage;
