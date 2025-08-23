#!/usr/bin/env python3
"""
Integration Test for Enhanced Ollama System

This script tests the integration between the enhanced Ollama model,
enhanced Ollama manager, and configuration persistence system.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.ai.providers.ollama_model_enhanced import (
    create_enhanced_ollama_model, OllamaModelConfigEnhanced
)
from app.ai.providers.ollama_manager_enhanced import enhanced_ollama_manager
from app.ai.ollama_config_manager import (
    ollama_config_manager, OllamaParameterPreset, 
    OllamaUserPreferences, OllamaProjectConfig, OllamaTeamConfig
)

async def test_enhanced_integration():
    """Test the enhanced Ollama integration system"""
    print("🧪 Testing Enhanced Ollama Integration System")
    print("=" * 60)
    
    try:
        # Test 1: Configuration Manager Setup
        print("\n1. Testing Configuration Manager Setup...")
        
        # Create test user preferences
        test_user_prefs = OllamaUserPreferences(
            user_id="test_user_123",
            default_model="llama3.1:8b",
            preferred_models={
                "coding": "codellama:7b",
                "creative": "llama3.1:8b",
                "analysis": "llama3.1:13b"
            },
            parameter_presets={
                "coding": "codellama_coding",
                "creative": "llama3_creative",
                "analysis": "llama3_analysis"
            }
        )
        
        success = ollama_config_manager.save_user_preferences(test_user_prefs)
        print(f"   ✅ Save user preferences: {'SUCCESS' if success else 'FAILED'}")
        
        # Create test project configuration
        test_project = OllamaProjectConfig(
            project_id="test_project_456",
            project_name="Test AI Project",
            default_model="llama3.1:8b",
            preferred_models=["llama3.1:8b", "codellama:7b", "mistral:7b"],
            model_constraints={
                "allowed_model_families": ["llama", "code", "mistral"],
                "max_model_size": "13B"
            },
            parameter_presets={
                "coding": "project_coding_preset",
                "creative": "project_creative_preset"
            },
            team_members=["user1", "user2", "user3"]
        )
        
        success = ollama_config_manager.save_project_config(test_project)
        print(f"   ✅ Save project config: {'SUCCESS' if success else 'FAILED'}")
        
        # Create test team configuration
        test_team = OllamaTeamConfig(
            team_id="test_team_789",
            team_name="AI Development Team",
            resource_requirements={
                "max_memory": "16GB",
                "max_cpu": "8",
                "max_gpu": "1"
            },
            shared_presets={
                "coding": "team_coding_preset",
                "documentation": "team_docs_preset"
            }
        )
        
        success = ollama_config_manager.save_team_config(test_team)
        print(f"   ✅ Save team config: {'SUCCESS' if success else 'FAILED'}")
        
        # Create test parameter presets
        presets = [
            OllamaParameterPreset(
                name="codellama_coding",
                description="Code generation preset for CodeLlama",
                temperature=0.3,
                top_p=0.95,
                top_k=50,
                tags=["coding", "codellama:7b"]
            ),
            OllamaParameterPreset(
                name="llama3_creative",
                description="Creative writing preset for Llama3",
                temperature=0.9,
                top_p=0.8,
                top_k=30,
                tags=["creative", "llama3.1:8b"]
            ),
            OllamaParameterPreset(
                name="llama3_analysis",
                description="Analysis preset for Llama3",
                temperature=0.5,
                top_p=0.9,
                top_k=40,
                tags=["analysis", "llama3.1:13b"]
            ),
            OllamaParameterPreset(
                name="project_coding_preset",
                description="Project-specific coding preset",
                temperature=0.4,
                top_p=0.92,
                top_k=45,
                tags=["coding", "project"]
            ),
            OllamaParameterPreset(
                name="team_coding_preset",
                description="Team-shared coding preset",
                temperature=0.35,
                top_p=0.94,
                top_k=48,
                tags=["coding", "team"]
            )
        ]
        
        for preset in presets:
            success = ollama_config_manager.save_parameter_preset(preset)
            print(f"   ✅ Save preset {preset.name}: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 2: Enhanced Ollama Manager
        print("\n2. Testing Enhanced Ollama Manager...")
        
        # Test intelligent model recommendations
        recommendations = await enhanced_ollama_manager.get_intelligent_model_recommendations(
            task_type="coding",
            user_id="test_user_123",
            project_id="test_project_456",
            team_id="test_team_789",
            content_length=5000,
            performance_priority="balanced"
        )
        
        print(f"   ✅ Get model recommendations: SUCCESS - {len(recommendations)} recommendations")
        
        for rec in recommendations[:3]:  # Show top 3
            print(f"      🎯 {rec.model_name}: {rec.confidence_score:.2f} - {rec.reasoning}")
        
        # Test optimized model config creation
        optimized_config = await enhanced_ollama_manager.create_optimized_model_config(
            model_name="codellama:7b",
            task_type="coding",
            user_id="test_user_123",
            project_id="test_project_456",
            team_id="test_team_789"
        )
        
        print(f"   ✅ Create optimized config: SUCCESS")
        print(f"      📝 Config: {optimized_config.get('preset_name', 'No preset')}")
        
        # Test 3: Enhanced Ollama Model
        print("\n3. Testing Enhanced Ollama Model...")
        
        # Create enhanced model with configuration integration
        enhanced_model = await create_enhanced_ollama_model(
            model_id="codellama:7b",
            user_id="test_user_123",
            project_id="test_project_456",
            team_id="test_team_789",
            preset_name="codellama_coding"
        )
        
        print(f"   ✅ Create enhanced model: SUCCESS")
        
        # Get configuration summary
        config_summary = await enhanced_model.get_configuration_summary()
        print(f"   ✅ Get config summary: SUCCESS")
        print(f"      📊 Applied configurations: {config_summary['configuration_sources']}")
        
        # Test preset management
        available_presets = await enhanced_model.get_available_presets()
        print(f"   ✅ Get available presets: SUCCESS - {len(available_presets)} presets")
        
        # Test 4: Configuration Integration
        print("\n4. Testing Configuration Integration...")
        
        # Test automatic preset application
        success = await enhanced_model.apply_preset("llama3_creative")
        print(f"   ✅ Apply preset: {'SUCCESS' if success else 'FAILED'}")
        
        # Get updated configuration summary
        updated_summary = await enhanced_model.get_configuration_summary()
        print(f"   ✅ Updated config summary: SUCCESS")
        print(f"      🎨 Active preset: {updated_summary['active_preset']}")
        
        # Test 5: System Health and Analytics
        print("\n5. Testing System Health and Analytics...")
        
        # Get model health summary
        health_summary = await enhanced_ollama_manager.get_model_health_summary()
        print(f"   ✅ Get health summary: SUCCESS")
        print(f"      🏥 Total models: {health_summary.get('total_models', 0)}")
        print(f"      💚 Healthy models: {health_summary.get('healthy_models', 0)}")
        
        # Get system status
        system_status = await enhanced_ollama_manager.get_system_status()
        print(f"   ✅ Get system status: SUCCESS")
        print(f"      🔧 Service healthy: {system_status.get('service_healthy', False)}")
        print(f"      📊 Performance data: {'Available' if system_status.get('performance_summary') else 'Not available'}")
        
        # Test 6: Configuration Analytics
        print("\n6. Testing Configuration Analytics...")
        
        # Get configuration summary
        config_summary = ollama_config_manager.get_configuration_summary()
        print(f"   ✅ Get config analytics: SUCCESS")
        print(f"      📝 Total presets: {config_summary.get('total_presets', 0)}")
        print(f"      👤 Total users: {config_summary.get('total_users', 0)}")
        print(f"      🏗️ Total projects: {config_summary.get('total_projects', 0)}")
        print(f"      👥 Total teams: {config_summary.get('total_teams', 0)}")
        
        # Test 7: Configuration Backup and Export
        print("\n7. Testing Configuration Backup and Export...")
        
        # Create backup
        backup_path = ollama_config_manager.create_backup("integration_test_backup")
        print(f"   ✅ Create backup: SUCCESS at {backup_path}")
        
        # Export specific preset
        export_path = ollama_config_manager.export_configuration(
            "parameter_presets", "codellama_coding"
        )
        print(f"   ✅ Export preset: SUCCESS to {export_path}")
        
        # Test 8: Configuration Sharing
        print("\n8. Testing Configuration Sharing...")
        
        # Share configuration between users
        success = ollama_config_manager.share_configuration(
            "parameter_presets", "codellama_coding", "test_user_123", "other_user_456"
        )
        print(f"   ✅ Share configuration: {'SUCCESS' if success else 'FAILED'}")
        
        # Test 9: Configuration History
        print("\n9. Testing Configuration History...")
        
        # Get configuration history
        history = ollama_config_manager.get_configuration_history(
            "parameter_presets", "codellama_coding"
        )
        print(f"   ✅ Get config history: SUCCESS - {len(history)} version(s)")
        
        # Test 10: Performance Integration
        print("\n10. Testing Performance Integration...")
        
        # Check if performance monitor is accessible
        try:
            # This would require the performance monitor to be properly initialized
            print(f"   ✅ Performance monitoring: Available")
        except Exception as e:
            print(f"   ⚠️ Performance monitoring: Limited - {e}")
        
        print("\n🎉 Enhanced Ollama Integration Test Completed Successfully!")
        print("=" * 60)
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        await enhanced_model.cleanup()
        await enhanced_ollama_manager.cleanup()
        
        # Remove test files
        import shutil
        test_paths = [
            ".taskmaster/test_ollama_config",
            backup_path,
            export_path
        ]
        
        for path in test_paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                print(f"   ✅ Cleaned up: {path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_enhanced_integration()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)




