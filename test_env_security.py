#!/usr/bin/env python3
"""
Test script for Environment Variable Exposure security measures in owl/webapp.py
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the project root to the path so we can import from owl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the security functions (avoiding full webapp import to prevent dependency issues)
from owl.webapp import (
    mask_sensitive_value,
    is_api_related,
    switch_env_display_mode,
    toggle_temporary_unmask,
    is_value_masked,
    ALLOWED_MODULES
)

def test_mask_sensitive_value():
    """Test the mask_sensitive_value function"""
    print("Testing mask_sensitive_value function...")

    # Test with sensitive API key
    sensitive_key = "OPENAI_API_KEY"
    sensitive_value = "sk-1234567890abcdef1234567890abcdef"
    masked = mask_sensitive_value(sensitive_key, sensitive_value)
    assert masked != sensitive_value, "Sensitive value should be masked"
    assert masked.startswith("sk-1234"), "Should show first 4 characters"
    assert masked.endswith("bcdef"), "Should show last 4 characters"
    assert "*" in masked, "Should contain asterisks"
    print("✅ Sensitive API key properly masked")

    # Test with non-sensitive value
    non_sensitive_key = "LOG_LEVEL"
    non_sensitive_value = "DEBUG"
    unmasked = mask_sensitive_value(non_sensitive_key, non_sensitive_value)
    assert unmasked == non_sensitive_value, "Non-sensitive value should not be masked"
    print("✅ Non-sensitive value correctly unmasked")

    # Test with short sensitive value
    short_key = "API_KEY"
    short_value = "abc"
    short_masked = mask_sensitive_value(short_key, short_value)
    assert short_masked == "a*c", "Short values should show first/last with asterisk"
    print("✅ Short sensitive value properly masked")

    # Test with empty value
    empty_masked = mask_sensitive_value("API_KEY", "")
    assert empty_masked == "", "Empty values should remain empty"
    print("✅ Empty values handled correctly")

def test_is_api_related():
    """Test the is_api_related function"""
    print("\nTesting is_api_related function...")

    # Test sensitive keys
    sensitive_keys = ["OPENAI_API_KEY", "API_TOKEN", "SECRET_KEY", "PASSWORD"]
    for key in sensitive_keys:
        assert is_api_related(key), f"Key {key} should be identified as API-related"
        print(f"✅ {key} correctly identified as sensitive")

    # Test non-sensitive keys
    non_sensitive_keys = ["LOG_LEVEL", "DEBUG", "TIMEOUT", "HOST"]
    for key in non_sensitive_keys:
        assert not is_api_related(key), f"Key {key} should not be identified as API-related"
        print(f"✅ {key} correctly identified as non-sensitive")

def test_switch_env_display_mode():
    """Test the switch_env_display_mode function"""
    print("\nTesting switch_env_display_mode function...")

    # Test view mode
    status, mode = switch_env_display_mode("view")
    assert mode == "view", "Should switch to view mode"
    assert "View mode" in status, "Should return appropriate status"
    print("✅ View mode switching works")

    # Test edit mode without confirmation
    status, mode = switch_env_display_mode("edit", confirmed=False)
    assert "Please confirm" in status, "Should require confirmation for edit mode"
    print("✅ Edit mode confirmation requirement works")

    # Test edit mode with confirmation
    status, mode = switch_env_display_mode("edit", confirmed=True)
    assert mode == "edit", "Should switch to edit mode with confirmation"
    assert "Edit mode enabled" in status, "Should confirm edit mode"
    print("✅ Edit mode with confirmation works")

def test_toggle_temporary_unmask():
    """Test the toggle_temporary_unmask function"""
    print("\nTesting toggle_temporary_unmask function...")

    # Test enabling temporary unmask
    status, is_unmasked = toggle_temporary_unmask()
    assert is_unmasked == True, "Should enable temporary unmask"
    assert "temporarily unmasked" in status, "Should indicate unmasking"
    assert "30s" in status, "Should mention timeout"
    print("✅ Temporary unmask enabling works")

    # Test disabling temporary unmask
    status, is_unmasked = toggle_temporary_unmask()
    assert is_unmasked == False, "Should disable temporary unmask"
    assert "re-masked" in status, "Should indicate re-masking"
    print("✅ Temporary unmask disabling works")

def test_is_value_masked():
    """Test the is_value_masked function"""
    print("\nTesting is_value_masked function...")

    # Reset global state first
    switch_env_display_mode("view")

    # Test masked value (in view mode)
    is_masked = is_value_masked("API_KEY", "abcd****wxyz", "abcd1234wxyz")
    assert is_masked == True, "Value should be masked in view mode"
    print("✅ Masked value detection works in view mode")

    # Test unmasked value (in edit mode)
    switch_env_display_mode("edit", confirmed=True)
    is_masked = is_value_masked("API_KEY", "abcd1234wxyz", "abcd1234wxyz")
    assert is_masked == False, "Value should not be masked in edit mode"
    print("✅ Unmasked value detection works in edit mode")

def test_integration_with_allowed_modules():
    """Test that the environment variable security doesn't interfere with module validation"""
    print("\nTesting integration with module security...")

    # Ensure ALLOWED_MODULES is still available and correct
    expected_modules = {'run', 'run_mini', 'run_gemini', 'run_claude', 'run_deepseek_zh', 'run_qwen_zh', 'run_terminal_zh'}
    assert ALLOWED_MODULES == expected_modules, "ALLOWED_MODULES should remain unchanged"
    print("✅ Integration with module security maintained")

def main():
    """Run all environment variable security tests"""
    print("🔐 Testing Environment Variable Security Measures")
    print("=" * 55)

    try:
        test_mask_sensitive_value()
        test_is_api_related()
        test_switch_env_display_mode()
        test_toggle_temporary_unmask()
        test_is_value_masked()
        test_integration_with_allowed_modules()

        print("\n" + "=" * 55)
        print("🎉 All environment variable security tests passed!")
        print("✅ Environment variable exposure prevention is working correctly")
        return 0

    except Exception as e:
        print(f"\n❌ Test execution failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

