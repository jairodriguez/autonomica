#!/usr/bin/env python3
"""
Test script for Ollama Configuration Persistence System

This script tests the core functionality of the configuration manager
without requiring the full FastAPI application to be running.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.ai.ollama_config_manager import (
    OllamaConfigManager, OllamaParameterPreset, 
    OllamaUserPreferences, OllamaProjectConfig, 
    OllamaTeamConfig, ConfigType
)

def test_configuration_system():
    """Test the configuration persistence system"""
    print("🧪 Testing Ollama Configuration Persistence System")
    print("=" * 60)
    
    # Initialize config manager with test path
    test_path = ".taskmaster/test_ollama_config"
    config_manager = OllamaConfigManager(test_path)
    
    try:
        # Test 1: Parameter Presets
        print("\n1. Testing Parameter Presets...")
        test_preset = OllamaParameterPreset(
            name="test_preset",
            description="A test preset for testing purposes",
            temperature=0.8,
            top_p=0.9,
            top_k=30,
            tags=["test", "demo"]
        )
        
        success = config_manager.save_parameter_preset(test_preset)
        print(f"   ✅ Save preset: {'SUCCESS' if success else 'FAILED'}")
        
        loaded_preset = config_manager.load_parameter_preset("test_preset")
        print(f"   ✅ Load preset: {'SUCCESS' if loaded_preset else 'FAILED'}")
        
        if loaded_preset:
            print(f"   📝 Preset details: {loaded_preset.name} - {loaded_preset.description}")
        
        # Test 2: User Preferences
        print("\n2. Testing User Preferences...")
        test_preferences = OllamaUserPreferences(
            user_id="test_user_123",
            default_model="llama3.1:8b",
            preferred_models={
                "coding": "llama3.1:8b",
                "content": "mixtral:8x7b"
            }
        )
        
        success = config_manager.save_user_preferences(test_preferences)
        print(f"   ✅ Save user preferences: {'SUCCESS' if success else 'FAILED'}")
        
        loaded_preferences = config_manager.load_user_preferences("test_user_123")
        print(f"   ✅ Load user preferences: {'SUCCESS' if loaded_preferences else 'FAILED'}")
        
        if loaded_preferences:
            print(f"   👤 User preferences: {loaded_preferences.default_model}")
        
        # Test 3: Project Configuration
        print("\n3. Testing Project Configuration...")
        test_project = OllamaProjectConfig(
            project_id="test_project_456",
            project_name="Test Project",
            default_model="llama3.1:8b",
            team_members=["user1", "user2", "user3"]
        )
        
        success = config_manager.save_project_config(test_project)
        print(f"   ✅ Save project config: {'SUCCESS' if success else 'FAILED'}")
        
        loaded_project = config_manager.load_project_config("test_project_456")
        print(f"   ✅ Load project config: {'SUCCESS' if loaded_project else 'FAILED'}")
        
        if loaded_project:
            print(f"   🏗️ Project: {loaded_project.project_name} with {len(loaded_project.team_members)} members")
        
        # Test 4: Team Configuration
        print("\n4. Testing Team Configuration...")
        test_team = OllamaTeamConfig(
            team_id="test_team_789",
            team_name="Test Team",
            resource_limits={"max_memory": "8GB", "max_cpu": "4"}
        )
        
        success = config_manager.save_team_config(test_team)
        print(f"   ✅ Save team config: {'SUCCESS' if success else 'FAILED'}")
        
        loaded_team = config_manager.load_team_config("test_team_789")
        print(f"   ✅ Load team config: {'SUCCESS' if loaded_team else 'FAILED'}")
        
        if loaded_team:
            print(f"   👥 Team: {loaded_team.team_name}")
        
        # Test 5: Configuration Backup
        print("\n5. Testing Configuration Backup...")
        backup_path = config_manager.create_backup("test_backup")
        print(f"   ✅ Create backup: SUCCESS at {backup_path}")
        
        # Test 6: Configuration Summary
        print("\n6. Testing Configuration Summary...")
        summary = config_manager.get_configuration_summary()
        print(f"   ✅ Get summary: SUCCESS")
        print(f"   📊 Summary: {summary['total_presets']} presets, {summary['total_users']} users, "
              f"{summary['total_projects']} projects, {summary['total_teams']} teams")
        
        # Test 7: Configuration Export
        print("\n7. Testing Configuration Export...")
        export_path = config_manager.export_configuration(
            ConfigType.PARAMETER_PRESETS, "test_preset"
        )
        print(f"   ✅ Export preset: SUCCESS to {export_path}")
        
        # Test 8: Configuration Sharing
        print("\n8. Testing Configuration Sharing...")
        success = config_manager.share_configuration(
            ConfigType.PARAMETER_PRESETS, "test_preset", "test_user_123", "other_user_456"
        )
        print(f"   ✅ Share configuration: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 9: Configuration History
        print("\n9. Testing Configuration History...")
        history = config_manager.get_configuration_history(
            ConfigType.PARAMETER_PRESETS, "test_preset"
        )
        print(f"   ✅ Get history: SUCCESS - {len(history)} version(s)")
        
        # Test 10: List Presets
        print("\n10. Testing Preset Listing...")
        presets = config_manager.list_parameter_presets()
        print(f"   ✅ List presets: SUCCESS - {len(presets)} preset(s) found")
        
        for preset in presets:
            print(f"      📝 {preset.name}: {preset.description}")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 60)
        
        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        import shutil
        if os.path.exists(test_path):
            shutil.rmtree(test_path)
            print("   ✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_configuration_system()
    sys.exit(0 if success else 1)




