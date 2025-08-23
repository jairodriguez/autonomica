#!/usr/bin/env python3
"""
Test script for the Error Handling System in owl/webapp.py
"""

import sys
import os
import tempfile

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_error_handling_system():
    """Test the comprehensive error handling system"""
    print("🚨 Testing Error Handling System")
    print("=" * 50)

    # Import the error handling components
    from owl.webapp import (
        ErrorHandlingService, ErrorSeverity, ErrorCategory, ErrorContext,
        UserFriendlyError, handle_authentication_error, handle_validation_error,
        handle_system_error, create_error_message, create_error_modal,
        create_error_statistics_dashboard, create_error_report
    )

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Setting up test environment...")

        # Create test error service
        error_service = ErrorHandlingService()
        error_service.users_file = os.path.join(temp_dir, "test_users.json")
        error_service.sessions_file = os.path.join(temp_dir, "test_sessions.json")
        error_service.security_log_file = os.path.join(temp_dir, "test_security.log")

        # Test 1: Error Service Initialization
        print("\n1. Testing Error Service Initialization")
        print("-" * 40)

        assert error_service.error_mappings is not None, "Error mappings should be initialized"
        assert len(error_service.error_mappings) > 0, "Should have default error mappings"
        assert "AUTH_INVALID_CREDENTIALS" in error_service.error_mappings, "Should have authentication errors"
        assert "VALIDATION_EMPTY_TASK" in error_service.error_mappings, "Should have validation errors"

        print("✅ Error service initialized correctly")

        # Test 2: Error Handling and Mapping
        print("\n2. Testing Error Handling and Mapping")
        print("-" * 40)

        # Test authentication error handling
        context = ErrorContext(
            user_id="test-user",
            component="test",
            operation="login_test"
        )

        auth_error = error_service.handle_error("AUTH_INVALID_CREDENTIALS", context)
        assert auth_error.code == "AUTH_INVALID_CREDENTIALS", "Should return correct error code"
        assert auth_error.title == "Invalid Login Credentials", "Should return user-friendly title"
        assert auth_error.severity == ErrorSeverity.MEDIUM, "Should have correct severity"
        assert auth_error.category == ErrorCategory.AUTHENTICATION, "Should have correct category"
        assert len(auth_error.suggested_solutions) > 0, "Should have suggested solutions"

        print("✅ Error handling and mapping works correctly")

        # Test 3: Error Context and Logging
        print("\n3. Testing Error Context and Logging")
        print("-" * 40)

        # Check that error was logged
        stats = error_service.get_error_stats()
        assert "AUTH_INVALID_CREDENTIALS" in stats, "Error should be tracked in statistics"
        assert stats["AUTH_INVALID_CREDENTIALS"] == 1, "Error count should be correct"

        # Check error history
        history = error_service.get_recent_errors(1)
        assert len(history) == 1, "Should have one error in history"
        assert history[0]['error']['code'] == "AUTH_INVALID_CREDENTIALS", "History should contain correct error"
        assert history[0]['context']['user_id'] == "test-user", "Context should be preserved"

        print("✅ Error context and logging works correctly")

        # Test 4: Helper Functions
        print("\n4. Testing Helper Functions")
        print("-" * 40)

        # Test authentication error helper
        auth_error_helper = handle_authentication_error("test-user", "127.0.0.1")
        assert auth_error_helper.title == "Invalid Login Credentials", "Helper should work correctly"

        # Test validation error helper
        validation_error_helper = handle_validation_error("task_description")
        assert validation_error_helper.title == "Task Description Required", "Validation helper should work"

        # Test system error helper
        system_error_helper = handle_system_error("test_operation")
        assert system_error_helper.title == "System Temporarily Unavailable", "System error helper should work"

        print("✅ Helper functions work correctly")

        # Test 5: Error UI Components
        print("\n5. Testing Error UI Components")
        print("-" * 40)

        # Test error message creation
        error_message_html = create_error_message(auth_error, show_detailed=True)
        assert "Invalid Login Credentials" in error_message_html, "Should contain error title"
        assert "❌" in error_message_html, "Should contain error icon"
        assert "Try Again" in error_message_html, "Should contain retry button"

        # Test error modal creation
        error_modal_html = create_error_modal(auth_error)
        assert "error-modal" in error_modal_html, "Should create modal structure"
        assert "Invalid Login Credentials" in error_modal_html, "Should contain error title"
        assert "Close" in error_modal_html, "Should have close button"

        print("✅ Error UI components work correctly")

        # Test 6: Error Statistics and Reporting
        print("\n6. Testing Error Statistics and Reporting")
        print("-" * 40)

        # Add more errors for testing
        error_service.handle_error("VALIDATION_EMPTY_TASK", context)
        error_service.handle_error("SYSTEM_UNAVAILABLE", context)

        # Test statistics
        stats = error_service.get_error_stats()
        assert len(stats) == 3, "Should have 3 different error types"
        assert stats["AUTH_INVALID_CREDENTIALS"] == 1, "Should have correct count"
        assert stats["VALIDATION_EMPTY_TASK"] == 1, "Should have correct count"

        # Test error report generation
        report = create_error_report()
        assert "Error Report" in report, "Should generate error report"
        assert "Total Errors: 3" in report, "Should have correct total"
        assert "Most Common Error: AUTH_INVALID_CREDENTIALS" in report, "Should identify most common error"

        # Test statistics dashboard
        dashboard = create_error_statistics_dashboard()
        assert "error-stats" in dashboard, "Should create dashboard structure"
        assert "Total Errors" in dashboard, "Should show total errors"

        print("✅ Error statistics and reporting works correctly")

        # Test 7: Error Recovery and Retry
        print("\n7. Testing Error Recovery and Retry")
        print("-" * 40)

        # Test errors with retry capability
        retry_error = error_service.error_mappings["AUTH_INVALID_CREDENTIALS"]
        assert retry_error.can_retry == True, "Authentication errors should be retryable"

        non_retry_error = error_service.error_mappings["AUTH_INSUFFICIENT_PRIVILEGES"]
        assert non_retry_error.can_retry == False, "Authorization errors should not be retryable"

        print("✅ Error recovery and retry logic works correctly")

        # Test 8: Error Categorization
        print("\n8. Testing Error Categorization")
        print("-" * 40)

        # Test different error categories
        auth_error = error_service.error_mappings["AUTH_INVALID_CREDENTIALS"]
        validation_error = error_service.error_mappings["VALIDATION_EMPTY_TASK"]
        system_error = error_service.error_mappings["SYSTEM_UNAVAILABLE"]

        assert auth_error.category == ErrorCategory.AUTHENTICATION, "Should categorize authentication errors"
        assert validation_error.category == ErrorCategory.VALIDATION, "Should categorize validation errors"
        assert system_error.category == ErrorCategory.SYSTEM, "Should categorize system errors"

        # Test severity levels
        assert auth_error.severity == ErrorSeverity.MEDIUM, "Authentication errors should be medium severity"
        assert system_error.severity == ErrorSeverity.HIGH, "System errors should be high severity"

        print("✅ Error categorization works correctly")

        # Test 9: Unknown Error Handling
        print("\n9. Testing Unknown Error Handling")
        print("-" * 40)

        # Test handling of unknown error codes
        unknown_error = error_service.handle_error("UNKNOWN_ERROR_CODE", context)
        assert unknown_error.code == "UNKNOWN_ERROR", "Should handle unknown errors gracefully"
        assert unknown_error.title == "Something Went Wrong", "Should provide fallback error message"
        assert unknown_error.suggested_solutions is not None, "Should have fallback solutions"

        print("✅ Unknown error handling works correctly")

        # Test 10: Error Service Management
        print("\n10. Testing Error Service Management")
        print("-" * 45)

        # Test clearing error history
        initial_count = len(error_service.error_history)
        error_service.clear_error_history()

        assert len(error_service.error_history) == 0, "Should clear error history"
        assert len(error_service.error_stats) == 0, "Should clear error statistics"

        # Verify service is still functional after clearing
        error_service.handle_error("AUTH_INVALID_CREDENTIALS", context)
        assert len(error_service.error_history) == 1, "Should still work after clearing"

        print("✅ Error service management works correctly")

        print("\n" + "=" * 50)
        print("🎉 Error Handling System Test Passed!")
        print("✅ All error handling components work correctly")
        print("✅ Task 5: Error Message System is complete!")

        return True

if __name__ == "__main__":
    try:
        success = test_error_handling_system()
        if success:
            print("\n✅ Task 5 Complete: Web Interface Error Message System Successfully Implemented!")
            exit(0)
        else:
            print("\n❌ Error handling system tests failed!")
            exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
