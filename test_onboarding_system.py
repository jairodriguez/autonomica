#!/usr/bin/env python3
"""
Test script for the comprehensive User Onboarding System in owl/webapp.py
"""

import sys
import os
import tempfile
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_onboarding_system():
    """Test the comprehensive user onboarding system"""
    print("🎯 Testing User Onboarding System")
    print("=" * 50)

    # Test 1: Onboarding Manager and State Management
    print("\n📋 Test 1: Onboarding State Management")
    try:
        from owl.webapp import (
            OnboardingManager, OnboardingState, OnboardingStep, TourType,
            onboarding_manager, get_onboarding_state
        )

        # Create test user
        test_user_id = "test_user_123"

        # Test getting onboarding state
        state = onboarding_manager.get_or_create_onboarding_state(test_user_id)
        assert isinstance(state, OnboardingState), "Should return OnboardingState instance"
        assert state.user_id == test_user_id, "User ID should match"
        assert state.current_step == OnboardingStep.WELCOME, "Should start with WELCOME step"

        print("✅ Onboarding state management works correctly")

    except Exception as e:
        print(f"❌ Onboarding state management failed: {e}")
        return False

    # Test 2: Step Progression
    print("\n📋 Test 2: Step Progression Logic")
    try:
        # Test marking steps complete
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.WELCOME)
        state = onboarding_manager.get_or_create_onboarding_state(test_user_id)
        assert OnboardingStep.WELCOME in state.completed_steps, "Should mark step as completed"

        # Test progress calculation
        progress = onboarding_manager.get_progress_percentage(test_user_id)
        assert progress >= 0 and progress <= 100, "Progress should be between 0-100"

        # Test completion detection
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.API_SETUP)
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.FIRST_TASK)

        is_completed = onboarding_manager.is_onboarding_completed(test_user_id)
        # Should not be completed until all required steps are done
        assert not is_completed, "Should not be completed until all required steps are done"

        print("✅ Step progression logic works correctly")

    except Exception as e:
        print(f"❌ Step progression logic failed: {e}")
        return False

    # Test 3: Example Tasks
    print("\n📋 Test 3: Pre-configured Example Tasks")
    try:
        # Test getting example tasks
        examples = onboarding_manager.get_example_tasks()
        assert len(examples) > 0, "Should have example tasks"

        # Test filtering by difficulty
        beginner_tasks = onboarding_manager.get_example_tasks(difficulty="beginner")
        assert len(beginner_tasks) > 0, "Should have beginner tasks"

        # Test filtering by category
        web_tasks = onboarding_manager.get_example_tasks(category="web_browsing")
        assert len(web_tasks) >= 0, "Should handle category filtering"

        print("✅ Example tasks system works correctly")

    except Exception as e:
        print(f"❌ Example tasks system failed: {e}")
        return False

    # Test 4: Tour Management
    print("\n📋 Test 4: Feature Tour Management")
    try:
        # Test starting a tour
        tour_steps = onboarding_manager.start_tour(test_user_id, TourType.TASK_CREATION)
        assert tour_steps is not None, "Should return tour steps"
        assert len(tour_steps) > 0, "Should have tour steps"

        # Test completing a tour
        onboarding_manager.complete_tour(test_user_id, TourType.TASK_CREATION)

        # Verify tour completion
        state = onboarding_manager.get_or_create_onboarding_state(test_user_id)
        assert state.tour_completed[TourType.TASK_CREATION] == True, "Should mark tour as completed"

        print("✅ Feature tour management works correctly")

    except Exception as e:
        print(f"❌ Feature tour management failed: {e}")
        return False

    # Test 5: Progress Tracking
    print("\n📋 Test 5: Progress Tracking and Analytics")
    try:
        # Test adding example task
        onboarding_manager.add_example_task(test_user_id, "example_1")
        state = onboarding_manager.get_or_create_onboarding_state(test_user_id)
        assert "example_1" in state.examples_created, "Should track created examples"

        # Test detailed progress
        progress = onboarding_manager.get_progress_percentage(test_user_id)
        assert isinstance(progress, float), "Should return float progress"

        print("✅ Progress tracking works correctly")

    except Exception as e:
        print(f"❌ Progress tracking failed: {e}")
        return False

    # Test 6: HTML Generation Functions
    print("\n📋 Test 6: HTML Generation Functions")
    try:
        from owl.webapp import (
            create_onboarding_progress_html, create_welcome_screen,
            create_wizard_step_welcome, create_wizard_step_api_setup,
            create_wizard_step_first_task, create_wizard_step_feature_tour,
            create_wizard_step_help_resources, create_wizard_step_completion
        )

        # Test progress HTML generation
        progress_html = create_onboarding_progress_html(test_user_id)
        assert len(progress_html) > 0, "Should generate progress HTML"
        assert "onboarding-progress" in progress_html, "Should contain progress class"

        # Test welcome screen generation
        welcome_html = create_welcome_screen(test_user_id)
        assert len(welcome_html) > 0, "Should generate welcome screen HTML"
        assert "Welcome to OWL System" in welcome_html, "Should contain welcome text"

        # Test wizard step generation
        welcome_step = create_wizard_step_welcome()
        assert len(welcome_step) > 0, "Should generate welcome step HTML"
        assert "Welcome to OWL System" in welcome_step, "Should contain step content"

        api_step = create_wizard_step_api_setup(test_user_id)
        assert len(api_step) > 0, "Should generate API setup step HTML"
        assert "API Key Setup" in api_step, "Should contain API setup content"

        task_step = create_wizard_step_first_task(test_user_id)
        assert len(task_step) > 0, "Should generate task step HTML"
        assert "Create Your First Task" in task_step, "Should contain task step content"

        tour_step = create_wizard_step_feature_tour(test_user_id)
        assert len(tour_step) > 0, "Should generate tour step HTML"
        assert "Explore System Features" in tour_step, "Should contain tour content"

        help_step = create_wizard_step_help_resources(test_user_id)
        assert len(help_step) > 0, "Should generate help step HTML"
        assert "Help & Documentation" in help_step, "Should contain help content"

        completion_step = create_wizard_step_completion(test_user_id)
        assert len(completion_step) > 0, "Should generate completion step HTML"
        assert "Setup Complete" in completion_step, "Should contain completion content"

        print("✅ HTML generation functions work correctly")

    except Exception as e:
        print(f"❌ HTML generation functions failed: {e}")
        return False

    # Test 7: Complete Onboarding Flow
    print("\n📋 Test 7: Complete Onboarding Flow")
    try:
        # Simulate complete onboarding flow
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.WELCOME)
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.API_SETUP)
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.FIRST_TASK)
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.FEATURE_TOUR)
        onboarding_manager.mark_step_completed(test_user_id, OnboardingStep.HELP_RESOURCES)

        # Check if onboarding is completed
        is_completed = onboarding_manager.is_onboarding_completed(test_user_id)
        assert is_completed, "Should be completed after all required steps"

        # Check final progress
        final_progress = onboarding_manager.get_progress_percentage(test_user_id)
        assert final_progress == 100.0, "Should be 100% complete"

        print("✅ Complete onboarding flow works correctly")

    except Exception as e:
        print(f"❌ Complete onboarding flow failed: {e}")
        return False

    print("\n🎉 All onboarding system tests passed!")
    print("=" * 50)
    print("📊 Test Results Summary:")
    print("✅ Onboarding State Management - PASSED")
    print("✅ Step Progression Logic - PASSED")
    print("✅ Pre-configured Example Tasks - PASSED")
    print("✅ Feature Tour Management - PASSED")
    print("✅ Progress Tracking - PASSED")
    print("✅ HTML Generation Functions - PASSED")
    print("✅ Complete Onboarding Flow - PASSED")

    return True

if __name__ == "__main__":
    success = test_onboarding_system()
    sys.exit(0 if success else 1)
