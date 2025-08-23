"""
Ollama Configuration Persistence System

Provides comprehensive configuration management for Ollama models including:
- User preference storage
- Per-project model configurations  
- Parameter presets for different use cases
- Configuration backup and restore functionality
- Configuration sharing between team members
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    TEAM = "team"
    WORKSPACE = "workspace"


class ConfigType(Enum):
    """Configuration types"""
    MODEL_PREFERENCES = "model_preferences"
    PARAMETER_PRESETS = "parameter_presets"
    PERFORMANCE_SETTINGS = "performance_settings"
    INTEGRATION_CONFIG = "integration_config"
    CUSTOM_SETTINGS = "custom_settings"


@dataclass
class OllamaParameterPreset:
    """Parameter preset for specific use cases"""
    name: str
    description: str
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    seed: Optional[int] = None
    num_ctx: Optional[int] = None
    num_gpu: Optional[int] = None
    num_thread: Optional[int] = None
    stop: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    usage_count: int = 0


@dataclass
class OllamaUserPreferences:
    """User-specific Ollama preferences"""
    user_id: str
    default_model: str = "llama3.1:8b"
    preferred_models: Dict[str, str] = field(default_factory=dict)  # task_type -> model_name
    parameter_presets: Dict[str, str] = field(default_factory=dict)  # task_type -> preset_name
    performance_settings: Dict[str, Any] = field(default_factory=dict)
    ui_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OllamaProjectConfig:
    """Project-specific Ollama configuration"""
    project_id: str
    project_name: str
    default_model: str = "llama3.1:8b"
    model_constraints: Dict[str, Any] = field(default_factory=dict)
    parameter_presets: Dict[str, str] = field(default_factory=dict)
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    team_members: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OllamaTeamConfig:
    """Team-wide Ollama configuration"""
    team_id: str
    team_name: str
    shared_presets: Dict[str, OllamaParameterPreset] = field(default_factory=dict)
    model_approvals: Dict[str, bool] = field(default_factory=dict)
    performance_standards: Dict[str, Any] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class OllamaConfigManager:
    """Comprehensive configuration management for Ollama"""
    
    def __init__(self, base_path: str = ".taskmaster/ollama_config"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Configuration storage paths
        self.presets_path = self.base_path / "presets"
        self.users_path = self.base_path / "users"
        self.projects_path = self.base_path / "projects"
        self.teams_path = self.base_path / "teams"
        self.backups_path = self.base_path / "backups"
        self.shared_path = self.base_path / "shared"
        
        # Create directory structure
        for path in [self.presets_path, self.users_path, self.projects_path, 
                    self.teams_path, self.backups_path, self.shared_path]:
            path.mkdir(exist_ok=True)
        
        # Database for configuration tracking
        self.db_path = self.base_path / "config.db"
        self._init_database()
        
        # Load default presets
        self._load_default_presets()
        
        logger.info(f"OllamaConfigManager initialized at {self.base_path}")
    
    def _init_database(self):
        """Initialize SQLite database for configuration tracking"""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_id TEXT NOT NULL,
                    version_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    change_description TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_sharing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_id TEXT NOT NULL,
                    shared_by TEXT NOT NULL,
                    shared_with TEXT NOT NULL,
                    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permissions TEXT DEFAULT 'read'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context TEXT
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _load_default_presets(self):
        """Load default parameter presets"""
        default_presets = {
            "creative_writing": OllamaParameterPreset(
                name="creative_writing",
                description="Optimized for creative writing and storytelling",
                temperature=0.9,
                top_p=0.95,
                top_k=50,
                repeat_penalty=1.05
            ),
            "code_generation": OllamaParameterPreset(
                name="code_generation", 
                description="Optimized for code generation and programming",
                temperature=0.3,
                top_p=0.8,
                top_k=20,
                repeat_penalty=1.2
            ),
            "analysis": OllamaParameterPreset(
                name="analysis",
                description="Optimized for analytical and factual responses",
                temperature=0.1,
                top_p=0.7,
                top_k=10,
                repeat_penalty=1.3
            ),
            "conversation": OllamaParameterPreset(
                name="conversation",
                description="Optimized for natural conversation",
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1
            ),
            "summarization": OllamaParameterPreset(
                name="summarization",
                description="Optimized for text summarization",
                temperature=0.2,
                top_p=0.8,
                top_k=15,
                repeat_penalty=1.25
            )
        }
        
        for preset in default_presets.values():
            self.save_parameter_preset(preset)
    
    def save_parameter_preset(self, preset: OllamaParameterPreset) -> bool:
        """Save a parameter preset"""
        try:
            preset.updated_at = datetime.utcnow()
            preset_path = self.presets_path / f"{preset.name}.json"
            
            with open(preset_path, 'w') as f:
                json.dump(asdict(preset), f, indent=2, default=str)
            
            # Track version
            self._track_config_version(ConfigType.PARAMETER_PRESETS, preset.name)
            
            logger.info(f"Saved parameter preset: {preset.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save parameter preset {preset.name}: {e}")
            return False
    
    def load_parameter_preset(self, name: str) -> Optional[OllamaParameterPreset]:
        """Load a parameter preset by name"""
        try:
            preset_path = self.presets_path / f"{name}.json"
            if not preset_path.exists():
                return None
            
            with open(preset_path, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return OllamaParameterPreset(**data)
            
        except Exception as e:
            logger.error(f"Failed to load parameter preset {name}: {e}")
            return None
    
    def list_parameter_presets(self) -> List[OllamaParameterPreset]:
        """List all available parameter presets"""
        presets = []
        for preset_file in self.presets_path.glob("*.json"):
            try:
                preset = self.load_parameter_preset(preset_file.stem)
                if preset:
                    presets.append(preset)
            except Exception as e:
                logger.warning(f"Failed to load preset {preset_file.stem}: {e}")
        
        return sorted(presets, key=lambda x: x.usage_count, reverse=True)
    
    def save_user_preferences(self, preferences: OllamaUserPreferences) -> bool:
        """Save user preferences"""
        try:
            preferences.updated_at = datetime.utcnow()
            user_path = self.users_path / f"{preferences.user_id}.json"
            
            with open(user_path, 'w') as f:
                json.dump(asdict(preferences), f, indent=2, default=str)
            
            # Track version
            self._track_config_version(ConfigType.MODEL_PREFERENCES, preferences.user_id)
            
            logger.info(f"Saved user preferences for {preferences.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save user preferences for {preferences.user_id}: {e}")
            return False
    
    def load_user_preferences(self, user_id: str) -> Optional[OllamaUserPreferences]:
        """Load user preferences by user ID"""
        try:
            user_path = self.users_path / f"{user_id}.json"
            if not user_path.exists():
                return None
            
            with open(user_path, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return OllamaUserPreferences(**data)
            
        except Exception as e:
            logger.error(f"Failed to load user preferences for {user_id}: {e}")
            return None
    
    def save_project_config(self, config: OllamaProjectConfig) -> bool:
        """Save project configuration"""
        try:
            config.updated_at = datetime.utcnow()
            project_path = self.projects_path / f"{config.project_id}.json"
            
            with open(project_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
            
            # Track version
            self._track_config_version(ConfigType.CUSTOM_SETTINGS, config.project_id)
            
            logger.info(f"Saved project config for {config.project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save project config for {config.project_id}: {e}")
            return False
    
    def load_project_config(self, project_id: str) -> Optional[OllamaProjectConfig]:
        """Load project configuration by project ID"""
        try:
            project_path = self.projects_path / f"{project_id}.json"
            if not project_path.exists():
                return None
            
            with open(project_path, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return OllamaProjectConfig(**data)
            
        except Exception as e:
            logger.error(f"Failed to load project config for {project_id}: {e}")
            return None
    
    def save_team_config(self, config: OllamaTeamConfig) -> bool:
        """Save team configuration"""
        try:
            config.updated_at = datetime.utcnow()
            team_path = self.teams_path / f"{config.team_id}.json"
            
            with open(team_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
            
            # Track version
            self._track_config_version(ConfigType.CUSTOM_SETTINGS, config.team_id)
            
            logger.info(f"Saved team config for {config.team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save team config for {config.team_id}: {e}")
            return False
    
    def load_team_config(self, team_id: str) -> Optional[OllamaTeamConfig]:
        """Load team configuration by team ID"""
        try:
            team_path = self.teams_path / f"{team_id}.json"
            if not team_path.exists():
                return None
            
            with open(team_path, 'r') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'created_at' in data:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if 'updated_at' in data:
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return OllamaTeamConfig(**data)
            
        except Exception as e:
            logger.error(f"Failed to load team config for {team_id}: {e}")
            return None
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of all configurations"""
        try:
            if not backup_name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_name = f"ollama_config_backup_{timestamp}"
            
            backup_path = self.backups_path / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # Copy all configuration files
            for source_dir in [self.presets_path, self.users_path, self.projects_path, self.teams_path]:
                if source_dir.exists():
                    dest_dir = backup_path / source_dir.name
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            
            # Copy database
            if self.db_path.exists():
                shutil.copy2(self.db_path, backup_path / "config.db")
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "created_at": datetime.utcnow().isoformat(),
                "source_path": str(self.base_path),
                "contents": {
                    "presets": len(list(self.presets_path.glob("*.json"))),
                    "users": len(list(self.users_path.glob("*.json"))),
                    "projects": len(list(self.projects_path.glob("*.json"))),
                    "teams": len(list(self.teams_path.glob("*.json")))
                }
            }
            
            with open(backup_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Created configuration backup: {backup_name}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore configuration from a backup"""
        try:
            backup_path = self.backups_path / backup_name
            if not backup_path.exists():
                raise ValueError(f"Backup {backup_name} not found")
            
            # Verify backup integrity
            manifest_path = backup_path / "manifest.json"
            if not manifest_path.exists():
                raise ValueError("Backup manifest not found")
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Create restore point
            restore_point = self.create_backup(f"restore_point_before_{backup_name}")
            
            # Restore configurations
            for source_dir in [self.presets_path, self.users_path, self.projects_path, self.teams_path]:
                if source_dir.exists():
                    shutil.rmtree(source_dir)
                
                backup_source = backup_path / source_dir.name
                if backup_source.exists():
                    shutil.copytree(backup_source, source_dir)
            
            # Restore database
            backup_db = backup_path / "config.db"
            if backup_db.exists():
                shutil.copy2(backup_db, self.db_path)
            
            logger.info(f"Restored configuration from backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_name}: {e}")
            return False
    
    def share_configuration(self, config_type: ConfigType, config_id: str, 
                          shared_by: str, shared_with: str, 
                          permissions: str = "read") -> bool:
        """Share configuration with another user/team"""
        try:
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO config_sharing 
                    (config_type, config_id, shared_by, shared_with, permissions)
                    VALUES (?, ?, ?, ?, ?)
                """, (config_type.value, config_id, shared_by, shared_with, permissions))
                conn.commit()
            
            logger.info(f"Shared {config_type.value} {config_id} from {shared_by} to {shared_with}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to share configuration: {e}")
            return False
    
    def get_shared_configurations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get configurations shared with a user"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT config_type, config_id, shared_by, permissions, shared_at
                    FROM config_sharing
                    WHERE shared_with = ?
                    ORDER BY shared_at DESC
                """, (user_id,))
                
                shared_configs = []
                for row in cursor.fetchall():
                    shared_configs.append({
                        "config_type": row[0],
                        "config_id": row[1],
                        "shared_by": row[2],
                        "permissions": row[3],
                        "shared_at": row[4]
                    })
                
                return shared_configs
                
        except Exception as e:
            logger.error(f"Failed to get shared configurations for {user_id}: {e}")
            return []
    
    def _track_config_version(self, config_type: ConfigType, config_id: str, 
                            user_id: Optional[str] = None, 
                            change_description: Optional[str] = None):
        """Track configuration version changes"""
        try:
            # Generate hash of current configuration
            config_hash = self._generate_config_hash(config_type, config_id)
            
            with self._get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO config_versions 
                    (config_type, config_id, version_hash, user_id, change_description)
                    VALUES (?, ?, ?, ?, ?)
                """, (config_type.value, config_id, config_hash, user_id, change_description))
                conn.commit()
                
        except Exception as e:
            logger.warning(f"Failed to track config version: {e}")
    
    def _generate_config_hash(self, config_type: ConfigType, config_id: str) -> str:
        """Generate hash for configuration content"""
        try:
            if config_type == ConfigType.PARAMETER_PRESETS:
                config_path = self.presets_path / f"{config_id}.json"
            elif config_type == ConfigType.MODEL_PREFERENCES:
                config_path = self.users_path / f"{config_id}.json"
            elif config_type == ConfigType.CUSTOM_SETTINGS:
                # Check both projects and teams
                config_path = self.projects_path / f"{config_id}.json"
                if not config_path.exists():
                    config_path = self.teams_path / f"{config_id}.json"
            else:
                return "unknown"
            
            if not config_path.exists():
                return "not_found"
            
            with open(config_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()[:16]
                
        except Exception as e:
            logger.warning(f"Failed to generate config hash: {e}")
            return "error"
    
    def get_configuration_history(self, config_type: ConfigType, config_id: str) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT version_hash, created_at, user_id, change_description
                    FROM config_versions
                    WHERE config_type = ? AND config_id = ?
                    ORDER BY created_at DESC
                """, (config_type.value, config_id))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        "version_hash": row[0],
                        "created_at": row[1],
                        "user_id": row[2],
                        "change_description": row[3]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get configuration history: {e}")
            return []
    
    def export_configuration(self, config_type: ConfigType, config_id: str, 
                           export_path: Optional[str] = None) -> str:
        """Export configuration to external file"""
        try:
            if not export_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                export_path = f"ollama_config_{config_type.value}_{config_id}_{timestamp}.json"
            
            export_path = Path(export_path)
            
            # Get configuration data
            if config_type == ConfigType.PARAMETER_PRESETS:
                config_data = self.load_parameter_preset(config_id)
            elif config_type == ConfigType.MODEL_PREFERENCES:
                config_data = self.load_user_preferences(config_id)
            elif config_type == ConfigType.CUSTOM_SETTINGS:
                config_data = self.load_project_config(config_id) or self.load_team_config(config_id)
            else:
                raise ValueError(f"Unsupported config type: {config_type}")
            
            if not config_data:
                raise ValueError(f"Configuration {config_id} not found")
            
            # Add metadata
            export_data = {
                "export_info": {
                    "exported_at": datetime.utcnow().isoformat(),
                    "config_type": config_type.value,
                    "config_id": config_id,
                    "version": "1.0"
                },
                "configuration": asdict(config_data)
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported configuration to {export_path}")
            return str(export_path)
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise
    
    def import_configuration(self, import_path: str, config_type: ConfigType, 
                           config_id: str, overwrite: bool = False) -> bool:
        """Import configuration from external file"""
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                raise ValueError(f"Import file {import_path} not found")
            
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate import data
            if "configuration" not in import_data:
                raise ValueError("Invalid import file format")
            
            config_data = import_data["configuration"]
            
            # Check if configuration already exists
            if not overwrite:
                if config_type == ConfigType.PARAMETER_PRESETS:
                    if self.load_parameter_preset(config_id):
                        raise ValueError(f"Preset {config_id} already exists. Use overwrite=True to replace.")
                elif config_type == ConfigType.MODEL_PREFERENCES:
                    if self.load_user_preferences(config_id):
                        raise ValueError(f"User preferences for {config_id} already exist. Use overwrite=True to replace.")
                elif config_type == ConfigType.CUSTOM_SETTINGS:
                    if self.load_project_config(config_id) or self.load_team_config(config_id):
                        raise ValueError(f"Configuration {config_id} already exists. Use overwrite=True to replace.")
            
            # Import configuration
            if config_type == ConfigType.PARAMETER_PRESETS:
                preset = OllamaParameterPreset(**config_data)
                preset.name = config_id  # Ensure correct name
                return self.save_parameter_preset(preset)
            elif config_type == ConfigType.MODEL_PREFERENCES:
                preferences = OllamaUserPreferences(**config_data)
                preferences.user_id = config_id  # Ensure correct user ID
                return self.save_user_preferences(preferences)
            elif config_type == ConfigType.CUSTOM_SETTINGS:
                # Try to determine if it's a project or team config
                if "project_name" in config_data:
                    project_config = OllamaProjectConfig(**config_data)
                    project_config.project_id = config_id
                    return self.save_project_config(project_config)
                elif "team_name" in config_data:
                    team_config = OllamaTeamConfig(**config_data)
                    team_config.team_id = config_id
                    return self.save_team_config(team_config)
                else:
                    raise ValueError("Cannot determine configuration type from import data")
            else:
                raise ValueError(f"Unsupported config type: {config_type}")
                
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of all configurations"""
        try:
            summary = {
                "total_presets": len(list(self.presets_path.glob("*.json"))),
                "total_users": len(list(self.users_path.glob("*.json"))),
                "total_projects": len(list(self.projects_path.glob("*.json"))),
                "total_teams": len(list(self.teams_path.glob("*.json"))),
                "total_backups": len(list(self.backups_path.glob("*"))),
                "recent_changes": [],
                "popular_presets": []
            }
            
            # Get recent changes
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT config_type, config_id, created_at, user_id
                    FROM config_versions
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                
                for row in cursor.fetchall():
                    summary["recent_changes"].append({
                        "config_type": row[0],
                        "config_id": row[1],
                        "created_at": row[2],
                        "user_id": row[3]
                    })
            
            # Get popular presets
            presets = self.list_parameter_presets()
            summary["popular_presets"] = [
                {"name": p.name, "usage_count": p.usage_count, "description": p.description}
                for p in sorted(presets, key=lambda x: x.usage_count, reverse=True)[:5]
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get configuration summary: {e}")
            return {}


# Global instance
ollama_config_manager = OllamaConfigManager()

