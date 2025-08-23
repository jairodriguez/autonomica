#!/usr/bin/env python3
"""
Test script for Authentication System in owl/webapp.py
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_authentication_system():
    """Test the authentication system components"""
    print("🔐 Testing Authentication System")
    print("=" * 50)

    # Import the authentication components
    from owl.webapp import (
        UserRole, User, Session, AuthenticationManager,
        hash_password, verify_password
    )

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Setting up test environment...")

        # Create test authentication manager
        auth_manager = AuthenticationManager()
        auth_manager.users_file = os.path.join(temp_dir, "test_users.json")
        auth_manager.sessions_file = os.path.join(temp_dir, "test_sessions.json")
        auth_manager.security_log_file = os.path.join(temp_dir, "test_security.log")

        # Test 1: User creation and password hashing
        print("\n1. Testing User Creation and Password Hashing")
        print("-" * 40)

        # Create test users
        admin_user = auth_manager.create_user("test_admin", "admin_pass", UserRole.ADMIN)
        regular_user = auth_manager.create_user("test_user", "user_pass", UserRole.USER)

        assert admin_user is not None, "Admin user should be created"
        assert regular_user is not None, "Regular user should be created"
        assert admin_user.role == UserRole.ADMIN, "Admin user should have admin role"
        assert regular_user.role == UserRole.USER, "Regular user should have user role"

        print("✅ User creation works correctly")
        print("✅ Password hashing is working")
        print("✅ Role assignment is correct")

        # Test 2: Password verification
        print("\n2. Testing Password Verification")
        print("-" * 40)

        assert auth_manager.verify_password("admin_pass", admin_user.password_hash), "Admin password should verify"
        assert auth_manager.verify_password("user_pass", regular_user.password_hash), "User password should verify"
        assert not auth_manager.verify_password("wrong_pass", admin_user.password_hash), "Wrong password should fail"

        print("✅ Password verification works correctly")

        # Test 3: User authentication
        print("\n3. Testing User Authentication")
        print("-" * 40)

        # Test successful authentication
        authenticated_admin = auth_manager.authenticate_user("test_admin", "admin_pass")
        authenticated_user = auth_manager.authenticate_user("test_user", "user_pass")

        assert authenticated_admin is not None, "Admin should authenticate successfully"
        assert authenticated_user is not None, "User should authenticate successfully"

        # Test failed authentication
        failed_auth = auth_manager.authenticate_user("test_admin", "wrong_pass")
        assert failed_auth is None, "Wrong password should fail authentication"

        print("✅ User authentication works correctly")
        print("✅ Failed authentication is handled properly")

        # Test 4: Session management
        print("\n4. Testing Session Management")
        print("-" * 40)

        # Create sessions
        admin_session = auth_manager.create_session(admin_user, "127.0.0.1", "Test-Agent")
        user_session = auth_manager.create_session(regular_user, "127.0.0.1", "Test-Agent")

        assert admin_session is not None, "Admin session should be created"
        assert user_session is not None, "User session should be created"
        assert admin_session.csrf_token is not None, "Session should have CSRF token"

        # Test session validation
        validated_admin = auth_manager.validate_session(admin_session.id)
        validated_user = auth_manager.validate_session(user_session.id)

        assert validated_admin is not None, "Admin session should validate"
        assert validated_user is not None, "User session should validate"

        # Test invalid session
        invalid_user = auth_manager.validate_session("invalid_session_id")
        assert invalid_user is None, "Invalid session should return None"

        print("✅ Session creation works correctly")
        print("✅ Session validation works correctly")
        print("✅ CSRF token generation works")

        # Test 5: Role-based permissions
        print("\n5. Testing Role-Based Permissions")
        print("-" * 40)

        admin_permissions = auth_manager.get_user_permissions(admin_user)
        user_permissions = auth_manager.get_user_permissions(regular_user)

        assert "view_admin_panel" in admin_permissions, "Admin should have admin panel access"
        assert "manage_users" in admin_permissions, "Admin should have user management access"
        assert "view_admin_panel" not in user_permissions, "Regular user should not have admin panel access"

        assert auth_manager.check_permission(admin_user, "manage_users"), "Admin should have manage_users permission"
        assert not auth_manager.check_permission(regular_user, "manage_users"), "Regular user should not have manage_users permission"

        print("✅ Role-based permissions work correctly")

        # Test 6: Account lockout
        print("\n6. Testing Account Lockout")
        print("-" * 40)

        # Simulate failed login attempts
        for i in range(5):
            auth_manager.authenticate_user("test_admin", "wrong_password")

        # Check if account is locked
        admin_user = auth_manager.users[admin_user.id]
        assert admin_user.locked_until is not None, "Account should be locked after 5 failed attempts"

        # Try to login with correct password (should fail due to lockout)
        locked_auth = auth_manager.authenticate_user("test_admin", "admin_pass")
        assert locked_auth is None, "Locked account should not authenticate"

        print("✅ Account lockout mechanism works correctly")

        # Test 7: Security logging
        print("\n7. Testing Security Logging")
        print("-" * 40)

        # Check if security log file was created
        assert os.path.exists(auth_manager.security_log_file), "Security log file should be created"

        # Read log entries
        with open(auth_manager.security_log_file, 'r') as f:
            logs = f.readlines()

        # Check for expected log entries
        log_content = ''.join(logs)
        assert "USER_CREATED" in log_content, "User creation should be logged"
        assert "LOGIN_SUCCESS" in log_content, "Successful login should be logged"
        assert "LOGIN_FAILED" in log_content, "Failed login should be logged"
        assert "ACCOUNT_LOCKED" in log_content, "Account lockout should be logged"

        print("✅ Security logging works correctly")

        print("\n" + "=" * 50)
        print("🎉 All authentication system tests passed!")
        print("✅ Authentication system is working correctly")

        return True

if __name__ == "__main__":
    try:
        success = test_authentication_system()
        if success:
            print("\n✅ Authentication system implementation is complete and functional!")
            exit(0)
        else:
            print("\n❌ Authentication system tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
