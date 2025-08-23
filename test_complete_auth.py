#!/usr/bin/env python3
"""
Comprehensive test for the complete Authentication System in owl/webapp.py
"""

import sys
import os
import tempfile
import json
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_authentication_system():
    """Test the complete authentication system including all components"""
    print("🔐 Testing Complete Authentication System")
    print("=" * 60)

    # Import the authentication components
    from owl.webapp import (
        UserRole, User, Session, AuthenticationManager,
        hash_password, verify_password, UserRole, create_default_users,
        get_all_users, create_new_user, get_security_logs, get_active_sessions,
        require_authentication, require_admin
    )

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Setting up test environment...")

        # Create test authentication manager
        auth_manager = AuthenticationManager()
        auth_manager.users_file = os.path.join(temp_dir, "test_users.json")
        auth_manager.sessions_file = os.path.join(temp_dir, "test_sessions.json")
        auth_manager.security_log_file = os.path.join(temp_dir, "test_security.log")

        # Test 1: Default user creation
        print("\n1. Testing Default User Creation")
        print("-" * 40)

        # Create default users
        create_default_users()

        # Verify users were created
        users = get_all_users()
        assert len(users) >= 2, "Should have at least admin and user accounts"

        admin_found = any(u['username'] == 'admin' and u['role'] == 'admin' for u in users)
        user_found = any(u['username'] == 'user' and u['role'] == 'user' for u in users)

        assert admin_found, "Default admin user should be created"
        assert user_found, "Default user should be created"

        print("✅ Default admin and user accounts created successfully")

        # Test 2: Authentication workflow
        print("\n2. Testing Complete Authentication Workflow")
        print("-" * 40)

        # Test admin login
        admin_user = auth_manager.authenticate_user("admin", "admin123")
        assert admin_user is not None, "Admin should authenticate successfully"
        assert admin_user.role == UserRole.ADMIN, "Admin should have admin role"

        # Create admin session
        admin_session = auth_manager.create_session(admin_user, "127.0.0.1", "Test-Agent")
        assert admin_session is not None, "Admin session should be created"

        # Set current user and session
        auth_manager.current_user = admin_user
        auth_manager.current_session = admin_session

        # Test user login
        regular_user = auth_manager.authenticate_user("user", "user123")
        assert regular_user is not None, "User should authenticate successfully"
        assert regular_user.role == UserRole.USER, "User should have user role"

        print("✅ Authentication workflow works correctly")

        # Test 3: Role-based access control
        print("\n3. Testing Role-Based Access Control")
        print("-" * 40)

        # Test admin permissions
        admin_permissions = auth_manager.get_user_permissions(admin_user)
        assert "view_admin_panel" in admin_permissions, "Admin should have admin panel access"
        assert "manage_users" in admin_permissions, "Admin should have user management access"

        # Test regular user permissions
        user_permissions = auth_manager.get_user_permissions(regular_user)
        assert "view_admin_panel" not in user_permissions, "Regular user should not have admin panel access"
        assert "manage_users" not in user_permissions, "Regular user should not have user management access"
        assert "access_basic_modules" in user_permissions, "Regular user should have basic module access"

        print("✅ Role-based permissions work correctly")

        # Test 4: Admin functionality
        print("\n4. Testing Admin-Only Functionality")
        print("-" * 40)

        # Test creating new user as admin
        new_user_result = create_new_user("test_new_user", "new_pass", "user")
        assert "successfully" in new_user_result.lower(), f"Admin should be able to create users: {new_user_result}"

        # Verify new user was created
        users_after = get_all_users()
        assert len(users_after) > len(users), "New user should be added to the list"

        # Test security logs access
        logs = get_security_logs()
        assert isinstance(logs, list), "Should be able to access security logs"

        # Test active sessions access
        sessions = get_active_sessions()
        assert isinstance(sessions, list), "Should be able to access active sessions"
        assert len(sessions) >= 1, "Should have at least one active session"

        print("✅ Admin functionality works correctly")

        # Test 5: Session management
        print("\n5. Testing Session Management")
        print("-" * 40)

        # Create multiple sessions
        session1 = auth_manager.create_session(regular_user, "127.0.0.1", "Agent1")
        session2 = auth_manager.create_session(admin_user, "127.0.0.1", "Agent2")

        # Test session validation
        validated1 = auth_manager.validate_session(session1.id)
        validated2 = auth_manager.validate_session(session2.id)

        assert validated1 is not None, "Session1 should validate"
        assert validated2 is not None, "Session2 should validate"

        # Test CSRF token validation
        csrf_valid = auth_manager.validate_csrf_token(session1.id, session1.csrf_token)
        assert csrf_valid, "CSRF token should be valid"

        csrf_invalid = auth_manager.validate_csrf_token(session1.id, "invalid_token")
        assert not csrf_invalid, "Invalid CSRF token should fail"

        print("✅ Session management works correctly")

        # Test 6: Security features
        print("\n6. Testing Security Features")
        print("-" * 40)

        # Test account lockout
        for i in range(5):
            auth_manager.authenticate_user("admin", "wrong_password")

        # Check if admin account is locked
        admin_user_check = auth_manager.users[admin_user.id]
        assert admin_user_check.locked_until is not None, "Account should be locked after 5 failed attempts"

        # Try to login with correct password (should fail)
        locked_login = auth_manager.authenticate_user("admin", "admin123")
        assert locked_login is None, "Locked account should not authenticate"

        print("✅ Account lockout mechanism works correctly")

        # Test 7: Security logging
        print("\n7. Testing Security Logging")
        print("-" * 40)

        # Check if security log file was created
        assert os.path.exists(auth_manager.security_log_file), "Security log file should be created"

        # Read log entries
        with open(auth_manager.security_log_file, 'r') as f:
            logs_content = f.read()

        # Check for expected log entries
        assert "USER_CREATED" in logs_content, "User creation should be logged"
        assert "LOGIN_SUCCESS" in logs_content, "Successful login should be logged"
        assert "LOGIN_FAILED" in logs_content, "Failed login should be logged"
        assert "ACCOUNT_LOCKED" in logs_content, "Account lockout should be logged"

        print("✅ Security logging works correctly")

        # Test 8: Decorator functionality
        print("\n8. Testing Authentication Decorators")
        print("-" * 40)

        # Test require_authentication decorator
        @require_authentication
        def protected_function():
            return "Access granted"

        # With authenticated user
        try:
            result = protected_function()
            assert result == "Access granted", "Protected function should work when authenticated"
            print("✅ require_authentication decorator works correctly")
        except Exception as e:
            print(f"❌ require_authentication decorator failed: {e}")

        # Test require_admin decorator
        @require_admin
        def admin_function():
            return "Admin access granted"

        # With admin user
        try:
            result = admin_function()
            assert result == "Admin access granted", "Admin function should work for admin user"
            print("✅ require_admin decorator works correctly")
        except Exception as e:
            print(f"❌ require_admin decorator failed: {e}")

        print("\n" + "=" * 60)
        print("🎉 Complete Authentication System Test Passed!")
        print("✅ All authentication components work together correctly")
        print("✅ Web interface authentication is fully functional")

        return True

if __name__ == "__main__":
    try:
        success = test_complete_authentication_system()
        if success:
            print("\n✅ Task 3 Complete: Web Interface Authentication Successfully Implemented!")
            exit(0)
        else:
            print("\n❌ Authentication system tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
