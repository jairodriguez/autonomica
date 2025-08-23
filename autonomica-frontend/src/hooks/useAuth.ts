import { useState, useEffect, useContext, createContext } from 'react';
import { useUser, useAuth as useClerkAuth } from '@clerk/nextjs';

interface User {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

interface UserPermissions {
  user_id: number;
  permissions: string[];
  role: string;
}

interface AuthContextType {
  user: User | null;
  permissions: string[];
  role: string;
  isLoading: boolean;
  isAuthenticated: boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const { user: clerkUser, isLoaded: clerkLoaded } = useUser();
  const { getToken } = useClerkAuth();
  
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [role, setRole] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchUserData = async () => {
    if (!clerkUser || !clerkLoaded) {
      setIsLoading(false);
      return;
    }

    try {
      const token = await getToken();
      
      // Fetch user data from our backend
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        
        // Fetch user permissions
        const permissionsResponse = await fetch('/api/auth/me/permissions', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (permissionsResponse.ok) {
          const permissionsData: UserPermissions = await permissionsResponse.json();
          setPermissions(permissionsData.permissions);
          setRole(permissionsData.role);
        }
      } else {
        console.error('Failed to fetch user data');
        setUser(null);
        setPermissions([]);
        setRole('');
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      setUser(null);
      setPermissions([]);
      setRole('');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, [clerkUser, clerkLoaded]);

  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission);
  };

  const hasAnyPermission = (permissionsList: string[]): boolean => {
    return permissionsList.some(permission => permissions.includes(permission));
  };

  const hasAllPermissions = (permissionsList: string[]): boolean => {
    return permissionsList.every(permission => permissions.includes(permission));
  };

  const hasRole = (userRole: string): boolean => {
    return role === userRole;
  };

  const hasAnyRole = (rolesList: string[]): boolean => {
    return rolesList.includes(role);
  };

  const refreshUser = async (): Promise<void> => {
    await fetchUserData();
  };

  const value: AuthContextType = {
    user,
    permissions,
    role,
    isLoading,
    isAuthenticated: !!user && user.is_active,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    refreshUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Permission constants for easy access
export const PERMISSIONS = {
  // Content Management
  CREATE_CONTENT: 'create_content',
  EDIT_CONTENT: 'edit_content',
  DELETE_CONTENT: 'delete_content',
  PUBLISH_CONTENT: 'publish_content',
  APPROVE_CONTENT: 'approve_content',
  
  // Social Media Management
  MANAGE_SOCIAL_ACCOUNTS: 'manage_social_accounts',
  SCHEDULE_POSTS: 'schedule_posts',
  PUBLISH_POSTS: 'publish_posts',
  VIEW_ANALYTICS: 'view_analytics',
  MANAGE_ANALYTICS: 'manage_analytics',
  
  // User Management
  MANAGE_USERS: 'manage_users',
  ASSIGN_ROLES: 'assign_roles',
  VIEW_USERS: 'view_users',
  
  // System Management
  MANAGE_SETTINGS: 'manage_settings',
  VIEW_LOGS: 'view_logs',
  MANAGE_INTEGRATIONS: 'manage_integrations'
} as const;

export const ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  EDITOR: 'editor',
  CREATOR: 'creator',
  VIEWER: 'viewer'
} as const;

// Permission groups for common use cases
export const PERMISSION_GROUPS = {
  CONTENT_MANAGEMENT: [
    PERMISSIONS.CREATE_CONTENT,
    PERMISSIONS.EDIT_CONTENT,
    PERMISSIONS.DELETE_CONTENT
  ],
  PUBLISHING: [
    PERMISSIONS.PUBLISH_CONTENT,
    PERMISSIONS.SCHEDULE_POSTS,
    PERMISSIONS.PUBLISH_POSTS
  ],
  ANALYTICS: [
    PERMISSIONS.VIEW_ANALYTICS
  ],
  USER_MANAGEMENT: [
    PERMISSIONS.MANAGE_USERS,
    PERMISSIONS.ASSIGN_ROLES,
    PERMISSIONS.VIEW_USERS
  ]
} as const;

// Role hierarchy for permission checking
export const ROLE_HIERARCHY = {
  [ROLES.ADMIN]: 5,
  [ROLES.MANAGER]: 4,
  [ROLES.EDITOR]: 3,
  [ROLES.CREATOR]: 2,
  [ROLES.VIEWER]: 1
} as const;

// Helper function to check if a role has higher privileges than another
export const hasHigherRole = (userRole: string, requiredRole: string): boolean => {
  const userLevel = ROLE_HIERARCHY[userRole as keyof typeof ROLE_HIERARCHY] || 0;
  const requiredLevel = ROLE_HIERARCHY[requiredRole as keyof typeof ROLE_HIERARCHY] || 0;
  return userLevel >= requiredLevel;
};




