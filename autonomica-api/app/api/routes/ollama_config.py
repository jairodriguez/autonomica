"""
Ollama Configuration Management API

Provides REST API endpoints for managing Ollama configurations including:
- User preferences
- Parameter presets
- Project configurations
- Team configurations
- Configuration backup/restore
- Configuration sharing
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import json
import tempfile
import os
from pathlib import Path

from app.ai.ollama_config_manager import (
    OllamaConfigManager, OllamaParameterPreset, OllamaUserPreferences,
    OllamaProjectConfig, OllamaTeamConfig, ConfigType, ConfigScope
)
from app.auth.dependencies import get_current_user
from app.models import ClerkUser

router = APIRouter(prefix="/api/ai/ollama/config", tags=["ollama-config"])

# Global config manager instance
config_manager = OllamaConfigManager()


# Parameter Presets Endpoints
@router.post("/presets", response_model=Dict[str, Any])
async def create_parameter_preset(
    preset: OllamaParameterPreset,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create a new parameter preset"""
    try:
        success = config_manager.save_parameter_preset(preset)
        if success:
            return {
                "success": True,
                "message": f"Parameter preset '{preset.name}' created successfully",
                "preset": preset
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create parameter preset")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets", response_model=List[OllamaParameterPreset])
async def list_parameter_presets():
    """List all available parameter presets"""
    try:
        return config_manager.list_parameter_presets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/presets/{preset_name}", response_model=OllamaParameterPreset)
async def get_parameter_preset(preset_name: str):
    """Get a specific parameter preset by name"""
    try:
        preset = config_manager.load_parameter_preset(preset_name)
        if preset:
            return preset
        else:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/presets/{preset_name}", response_model=Dict[str, Any])
async def update_parameter_preset(
    preset_name: str,
    preset: OllamaParameterPreset,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Update an existing parameter preset"""
    try:
        # Ensure the name matches the path parameter
        preset.name = preset_name
        
        success = config_manager.save_parameter_preset(preset)
        if success:
            return {
                "success": True,
                "message": f"Parameter preset '{preset_name}' updated successfully",
                "preset": preset
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update parameter preset")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/presets/{preset_name}", response_model=Dict[str, Any])
async def delete_parameter_preset(
    preset_name: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Delete a parameter preset"""
    try:
        preset_path = config_manager.presets_path / f"{preset_name}.json"
        if preset_path.exists():
            preset_path.unlink()
            return {
                "success": True,
                "message": f"Parameter preset '{preset_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User Preferences Endpoints
@router.post("/users/{user_id}/preferences", response_model=Dict[str, Any])
async def create_user_preferences(
    user_id: str,
    preferences: OllamaUserPreferences,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create or update user preferences"""
    try:
        # Ensure the user ID matches the path parameter
        preferences.user_id = user_id
        
        success = config_manager.save_user_preferences(preferences)
        if success:
            return {
                "success": True,
                "message": f"User preferences for '{user_id}' saved successfully",
                "preferences": preferences
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save user preferences")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/preferences", response_model=OllamaUserPreferences)
async def get_user_preferences(
    user_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get user preferences by user ID"""
    try:
        preferences = config_manager.load_user_preferences(user_id)
        if preferences:
            return preferences
        else:
            raise HTTPException(status_code=404, detail=f"User preferences for '{user_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}/preferences", response_model=Dict[str, Any])
async def update_user_preferences(
    user_id: str,
    preferences: OllamaUserPreferences,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Update user preferences"""
    try:
        # Ensure the user ID matches the path parameter
        preferences.user_id = user_id
        
        success = config_manager.save_user_preferences(preferences)
        if success:
            return {
                "success": True,
                "message": f"User preferences for '{user_id}' updated successfully",
                "preferences": preferences
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update user preferences")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Project Configuration Endpoints
@router.post("/projects", response_model=Dict[str, Any])
async def create_project_config(
    config: OllamaProjectConfig,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create a new project configuration"""
    try:
        success = config_manager.save_project_config(config)
        if success:
            return {
                "success": True,
                "message": f"Project configuration '{config.project_name}' created successfully",
                "config": config
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create project configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}", response_model=OllamaProjectConfig)
async def get_project_config(project_id: str):
    """Get project configuration by project ID"""
    try:
        config = config_manager.load_project_config(project_id)
        if config:
            return config
        else:
            raise HTTPException(status_code=404, detail=f"Project configuration '{project_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_id}", response_model=Dict[str, Any])
async def update_project_config(
    project_id: str,
    config: OllamaProjectConfig,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Update project configuration"""
    try:
        # Ensure the project ID matches the path parameter
        config.project_id = project_id
        
        success = config_manager.save_project_config(config)
        if success:
            return {
                "success": True,
                "message": f"Project configuration '{project_id}' updated successfully",
                "config": config
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update project configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}", response_model=Dict[str, Any])
async def delete_project_config(
    project_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Delete project configuration"""
    try:
        project_path = config_manager.projects_path / f"{project_id}.json"
        if project_path.exists():
            project_path.unlink()
            return {
                "success": True,
                "message": f"Project configuration '{project_id}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Project configuration '{project_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Team Configuration Endpoints
@router.post("/teams", response_model=Dict[str, Any])
async def create_team_config(
    config: OllamaTeamConfig,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create a new team configuration"""
    try:
        success = config_manager.save_team_config(config)
        if success:
            return {
                "success": True,
                "message": f"Team configuration '{config.team_name}' created successfully",
                "config": config
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create team configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}", response_model=OllamaTeamConfig)
async def get_team_config(team_id: str):
    """Get team configuration by team ID"""
    try:
        config = config_manager.load_team_config(team_id)
        if config:
            return config
        else:
            raise HTTPException(status_code=404, detail=f"Team configuration '{team_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/teams/{team_id}", response_model=Dict[str, Any])
async def update_team_config(
    team_id: str,
    config: OllamaTeamConfig,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Update team configuration"""
    try:
        # Ensure the team ID matches the path parameter
        config.team_id = team_id
        
        success = config_manager.save_team_config(config)
        if success:
            return {
                "success": True,
                "message": f"Team configuration '{team_id}' updated successfully",
                "config": config
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update team configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}", response_model=Dict[str, Any])
async def delete_team_config(
    team_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Delete team configuration"""
    try:
        team_path = config_manager.teams_path / f"{team_id}.json"
        if team_path.exists():
            team_path.unlink()
            return {
                "success": True,
                "message": f"Team configuration '{team_id}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Team configuration '{team_id}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Backup and Restore Endpoints
@router.post("/backup", response_model=Dict[str, Any])
async def create_configuration_backup(
    backup_name: Optional[str] = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create a backup of all configurations"""
    try:
        backup_path = config_manager.create_backup(backup_name)
        return {
            "success": True,
            "message": "Configuration backup created successfully",
            "backup_path": backup_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup", response_model=List[Dict[str, Any]])
async def list_backups():
    """List all available backups"""
    try:
        backups = []
        for backup_dir in config_manager.backups_path.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    backups.append(manifest)
        
        return sorted(backups, key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backup/{backup_name}/restore", response_model=Dict[str, Any])
async def restore_configuration_backup(
    backup_name: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Restore configuration from a backup"""
    try:
        success = config_manager.restore_backup(backup_name)
        if success:
            return {
                "success": True,
                "message": f"Configuration restored from backup '{backup_name}' successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to restore configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backup/{backup_name}", response_model=Dict[str, Any])
async def delete_backup(
    backup_name: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Delete a configuration backup"""
    try:
        backup_path = config_manager.backups_path / backup_name
        if backup_path.exists():
            import shutil
            shutil.rmtree(backup_path)
            return {
                "success": True,
                "message": f"Backup '{backup_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Backup '{backup_name}' not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Export/Import Endpoints
@router.get("/export/{config_type}/{config_id}")
async def export_configuration(
    config_type: str,
    config_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Export configuration to a file"""
    try:
        # Convert string to ConfigType enum
        try:
            config_type_enum = ConfigType(config_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {config_type}")
        
        export_path = config_manager.export_configuration(config_type_enum, config_id)
        
        # Return the file for download
        return FileResponse(
            path=export_path,
            filename=os.path.basename(export_path),
            media_type='application/json'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/{config_type}/{config_id}")
async def import_configuration(
    config_type: str,
    config_id: str,
    overwrite: bool = False,
    file: UploadFile = File(...),
    current_user: ClerkUser = Depends(get_current_user)
):
    """Import configuration from a file"""
    try:
        # Convert string to ConfigType enum
        try:
            config_type_enum = ConfigType(config_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {config_type}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            success = config_manager.import_configuration(
                temp_file_path, config_type_enum, config_id, overwrite
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Configuration imported successfully"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to import configuration")
                
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Sharing Endpoints
@router.post("/share", response_model=Dict[str, Any])
async def share_configuration(
    config_type: str,
    config_id: str,
    shared_with: str,
    permissions: str = "read",
    current_user: ClerkUser = Depends(get_current_user)
):
    """Share configuration with another user/team"""
    try:
        # Convert string to ConfigType enum
        try:
            config_type_enum = ConfigType(config_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {config_type}")
        
        success = config_manager.share_configuration(
            config_type_enum, config_id, current_user.id, shared_with, permissions
        )
        
        if success:
            return {
                "success": True,
                "message": f"Configuration shared successfully with {shared_with}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to share configuration")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shared", response_model=List[Dict[str, Any]])
async def get_shared_configurations(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get configurations shared with the current user"""
    try:
        return config_manager.get_shared_configurations(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration History Endpoints
@router.get("/history/{config_type}/{config_id}", response_model=List[Dict[str, Any]])
async def get_configuration_history(
    config_type: str,
    config_id: str
):
    """Get configuration change history"""
    try:
        # Convert string to ConfigType enum
        try:
            config_type_enum = ConfigType(config_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {config_type}")
        
        return config_manager.get_configuration_history(config_type_enum, config_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Summary Endpoint
@router.get("/summary", response_model=Dict[str, Any])
async def get_configuration_summary():
    """Get summary of all configurations"""
    try:
        return config_manager.get_configuration_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint
@router.get("/health", response_model=Dict[str, Any])
async def config_health_check():
    """Health check for configuration system"""
    try:
        # Check if all directories exist
        directories_exist = all([
            config_manager.presets_path.exists(),
            config_manager.users_path.exists(),
            config_manager.projects_path.exists(),
            config_manager.teams_path.exists(),
            config_manager.backups_path.exists(),
            config_manager.shared_path.exists()
        ])
        
        # Check if database is accessible
        db_accessible = config_manager.db_path.exists()
        
        # Get basic stats
        summary = config_manager.get_configuration_summary()
        
        return {
            "status": "healthy" if directories_exist and db_accessible else "unhealthy",
            "directories_exist": directories_exist,
            "database_accessible": db_accessible,
            "summary": summary
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

