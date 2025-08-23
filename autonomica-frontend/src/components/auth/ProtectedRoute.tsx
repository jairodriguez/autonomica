import React from 'react';
import { useAuth, PERMISSIONS, ROLES } from '../../hooks/useAuth';
import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import { AccessDenied } from '@mui/icons-material';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredPermissions?: string[];
  requiredRoles?: string[];
  requireAllPermissions?: boolean;
  requireAllRoles?: boolean;
  fallback?: React.ReactNode;
  showAccessDenied?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredPermissions = [],
  requiredRoles = [],
  requireAllPermissions = true,
  requireAllRoles = false,
  fallback,
  showAccessDenied = true
}) => {
  const { 
    user, 
    permissions, 
    role, 
    isLoading, 
    isAuthenticated,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole
  } = useAuth();

  // Show loading state while authentication is being determined
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  // Check if user is authenticated
  if (!isAuthenticated) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Alert severity="warning">
          Please sign in to access this content.
        </Alert>
      </Box>
    );
  }

  // Check role requirements
  let hasRequiredRole = true;
  if (requiredRoles.length > 0) {
    if (requireAllRoles) {
      hasRequiredRole = hasAllPermissions(requiredRoles);
    } else {
      hasRequiredRole = hasAnyRole(requiredRoles);
    }
  }

  // Check permission requirements
  let hasRequiredPermissions = true;
  if (requiredPermissions.length > 0) {
    if (requireAllPermissions) {
      hasRequiredPermissions = hasAllPermissions(requiredPermissions);
    } else {
      hasRequiredPermissions = hasAnyPermission(requiredPermissions);
    }
  }

  // If all checks pass, render children
  if (hasRequiredRole && hasRequiredPermissions) {
    return <>{children}</>;
  }

  // If custom fallback is provided, use it
  if (fallback) {
    return <>{fallback}</>;
  }

  // Show access denied message
  if (showAccessDenied) {
    return (
      <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="200px" gap={2}>
        <AccessDenied color="error" sx={{ fontSize: 64 }} />
        <Typography variant="h6" color="error">
          Access Denied
        </Typography>
        <Typography variant="body2" color="textSecondary" textAlign="center" maxWidth="400px">
          You don't have the required permissions to access this content.
          {requiredPermissions.length > 0 && (
            <>
              <br />
              Required permissions: {requiredPermissions.join(', ')}
            </>
          )}
          {requiredRoles.length > 0 && (
            <>
              <br />
              Required roles: {requiredRoles.join(', ')}
            </>
          )}
        </Typography>
      </Box>
    );
  }

  // If no fallback and access denied is hidden, render nothing
  return null;
};

// Convenience components for common permission patterns
export const ContentManagementRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute
    requiredPermissions={[PERMISSIONS.CREATE_CONTENT, PERMISSIONS.EDIT_CONTENT, PERMISSIONS.DELETE_CONTENT]}
    requireAllPermissions={false}
  >
    {children}
  </ProtectedRoute>
);

export const PublishingRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute
    requiredPermissions={[PERMISSIONS.PUBLISH_CONTENT, PERMISSIONS.SCHEDULE_POSTS, PERMISSIONS.PUBLISH_POSTS]}
    requireAllPermissions={false}
  >
    {children}
  </ProtectedRoute>
);

export const AnalyticsRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredPermissions={[PERMISSIONS.VIEW_ANALYTICS]}>
    {children}
  </ProtectedRoute>
);

export const UserManagementRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute
    requiredPermissions={[PERMISSIONS.MANAGE_USERS, PERMISSIONS.ASSIGN_ROLES, PERMISSIONS.VIEW_USERS]}
    requireAllPermissions={false}
  >
    {children}
  </ProtectedRoute>
);

export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles={[ROLES.ADMIN]}>
    {children}
  </ProtectedRoute>
);

export const ManagerOrAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles={[ROLES.MANAGER, ROLES.ADMIN]} requireAllRoles={false}>
    {children}
  </ProtectedRoute>
);

export const EditorOrHigherRoute: React.FC<{ children: React.FC<{ children: React.ReactNode }> }> = ({ children }) => (
  <ProtectedRoute requiredRoles={[ROLES.EDITOR, ROLES.MANAGER, ROLES.ADMIN]} requireAllRoles={false}>
    {children}
  </ProtectedRoute>
);

export const CreatorOrHigherRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles={[ROLES.CREATOR, ROLES.EDITOR, ROLES.MANAGER, ROLES.ADMIN]} requireAllRoles={false}>
    {children}
  </ProtectedRoute>
);

export default ProtectedRoute;




