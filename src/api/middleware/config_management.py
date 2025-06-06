from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import hashlib
from redis.asyncio import Redis
from enum import Enum

class ConfigStatus(Enum):
    """Configuration status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

@dataclass
class ConfigVersion:
    """Configuration version."""
    id: str
    version: int
    config_data: Dict[str, Any]
    status: ConfigStatus
    created_by: str
    created_at: datetime
    description: str
    checksum: str

class ConfigurationManager:
    """Configuration management for rate limiting with version control."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.configs_key = "rate_limit:configs"
        self.versions_key = "rate_limit:config_versions:{}"
        self.active_config_key = "rate_limit:active_config"
    
    async def create_config(
        self,
        config_id: str,
        config_data: Dict[str, Any],
        created_by: str,
        description: str = ""
    ) -> ConfigVersion:
        """Create a new configuration version."""
        # Generate checksum
        config_json = json.dumps(config_data, sort_keys=True)
        checksum = hashlib.sha256(config_json.encode()).hexdigest()
        
        # Get next version number
        version = await self._get_next_version(config_id)
        
        config_version = ConfigVersion(
            id=config_id,
            version=version,
            config_data=config_data,
            status=ConfigStatus.DRAFT,
            created_by=created_by,
            created_at=datetime.now(),
            description=description,
            checksum=checksum
        )
        
        # Store version
        await self._store_version(config_version)
        
        return config_version
    
    async def activate_config(self, config_id: str, version: int) -> bool:
        """Activate a configuration version."""
        try:
            config_version = await self.get_config_version(config_id, version)
            if not config_version:
                return False
            
            # Deactivate current active config
            current_active = await self.get_active_config()
            if current_active:
                current_active.status = ConfigStatus.ARCHIVED
                await self._store_version(current_active)
            
            # Activate new config
            config_version.status = ConfigStatus.ACTIVE
            await self._store_version(config_version)
            
            # Set as active
            await self.redis.set(
                self.active_config_key,
                json.dumps({
                    "config_id": config_id,
                    "version": version,
                    "activated_at": datetime.now().isoformat()
                })
            )
            
            return True
        except Exception as e:
            print(f"Failed to activate config {config_id}:{version}: {e}")
            return False
    
    async def get_active_config(self) -> Optional[ConfigVersion]:
        """Get the currently active configuration."""
        active_data = await self.redis.get(self.active_config_key)
        if not active_data:
            return None
        
        active_info = json.loads(active_data)
        return await self.get_config_version(
            active_info["config_id"],
            active_info["version"]
        )
    
    async def get_config_version(
        self,
        config_id: str,
        version: int
    ) -> Optional[ConfigVersion]:
        """Get a specific configuration version."""
        versions_key = self.versions_key.format(config_id)
        version_data = await self.redis.hget(versions_key, str(version))
        
        if not version_data:
            return None
        
        data = json.loads(version_data)
        return ConfigVersion(
            id=data["id"],
            version=data["version"],
            config_data=data["config_data"],
            status=ConfigStatus(data["status"]),
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
            description=data["description"],
            checksum=data["checksum"]
        )
    
    async def list_config_versions(self, config_id: str) -> List[ConfigVersion]:
        """List all versions of a configuration."""
        versions_key = self.versions_key.format(config_id)
        all_versions = await self.redis.hgetall(versions_key)
        
        versions = []
        for version_num, version_data in all_versions.items():
            data = json.loads(version_data)
            versions.append(ConfigVersion(
                id=data["id"],
                version=int(version_num),
                config_data=data["config_data"],
                status=ConfigStatus(data["status"]),
                created_by=data["created_by"],
                created_at=datetime.fromisoformat(data["created_at"]),
                description=data["description"],
                checksum=data["checksum"]
            ))
        
        return sorted(versions, key=lambda x: x.version, reverse=True)
    
    async def rollback_to_version(
        self,
        config_id: str,
        version: int,
        rolled_back_by: str
    ) -> bool:
        """Rollback to a previous configuration version."""
        try:
            # Get the target version
            target_version = await self.get_config_version(config_id, version)
            if not target_version:
                return False
            
            # Create a new version with the same config data
            rollback_config = await self.create_config(
                config_id=config_id,
                config_data=target_version.config_data,
                created_by=rolled_back_by,
                description=f"Rollback to version {version}"
            )
            
            # Activate the rollback config
            return await self.activate_config(config_id, rollback_config.version)
        except Exception as e:
            print(f"Failed to rollback config {config_id} to version {version}: {e}")
            return False
    
    async def compare_versions(
        self,
        config_id: str,
        version1: int,
        version2: int
    ) -> Dict[str, Any]:
        """Compare two configuration versions."""
        v1 = await self.get_config_version(config_id, version1)
        v2 = await self.get_config_version(config_id, version2)
        
        if not v1 or not v2:
            return {}
        
        # Simple diff implementation
        diff = {
            "version1": {
                "version": v1.version,
                "created_at": v1.created_at.isoformat(),
                "created_by": v1.created_by,
                "checksum": v1.checksum
            },
            "version2": {
                "version": v2.version,
                "created_at": v2.created_at.isoformat(),
                "created_by": v2.created_by,
                "checksum": v2.checksum
            },
            "changes": self._compute_diff(v1.config_data, v2.config_data)
        }
        
        return diff
    
    def _compute_diff(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compute differences between two configurations."""
        changes = []
        
        # Check for added/modified keys
        for key, value in config2.items():
            if key not in config1:
                changes.append({
                    "type": "added",
                    "key": key,
                    "value": value
                })
            elif config1[key] != value:
                changes.append({
                    "type": "modified",
                    "key": key,
                    "old_value": config1[key],
                    "new_value": value
                })
        
        # Check for removed keys
        for key in config1:
            if key not in config2:
                changes.append({
                    "type": "removed",
                    "key": key,
                    "value": config1[key]
                })
        
        return changes
    
    async def validate_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate a configuration."""
        errors = []
        
        # Basic validation rules
        required_fields = ["rate_limits", "categories"]
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate rate limits
        if "rate_limits" in config_data:
            for category, limits in config_data["rate_limits"].items():
                if not isinstance(limits, dict):
                    errors.append(f"Rate limits for {category} must be a dictionary")
                    continue
                
                required_limit_fields = ["requests_per_minute", "burst_multiplier"]
                for field in required_limit_fields:
                    if field not in limits:
                        errors.append(f"Missing {field} in rate limits for {category}")
                    elif not isinstance(limits[field], (int, float)):
                        errors.append(f"{field} must be a number for {category}")
        
        return errors
    
    async def export_config(self, config_id: str, version: int) -> Optional[str]:
        """Export a configuration as JSON."""
        config_version = await self.get_config_version(config_id, version)
        if not config_version:
            return None
        
        export_data = {
            "metadata": {
                "config_id": config_version.id,
                "version": config_version.version,
                "created_by": config_version.created_by,
                "created_at": config_version.created_at.isoformat(),
                "description": config_version.description,
                "checksum": config_version.checksum
            },
            "config": config_version.config_data
        }
        
        return json.dumps(export_data, indent=2)
    
    async def import_config(
        self,
        config_json: str,
        imported_by: str,
        new_config_id: Optional[str] = None
    ) -> Optional[ConfigVersion]:
        """Import a configuration from JSON."""
        try:
            import_data = json.loads(config_json)
            
            config_id = new_config_id or import_data["metadata"]["config_id"]
            config_data = import_data["config"]
            description = f"Imported from {import_data['metadata']['config_id']}:{import_data['metadata']['version']}"
            
            # Validate config before importing
            errors = await self.validate_config(config_data)
            if errors:
                raise ValueError(f"Invalid configuration: {', '.join(errors)}")
            
            return await self.create_config(
                config_id=config_id,
                config_data=config_data,
                created_by=imported_by,
                description=description
            )
        except Exception as e:
            print(f"Failed to import config: {e}")
            return None
    
    async def _get_next_version(self, config_id: str) -> int:
        """Get the next version number for a config."""
        versions_key = self.versions_key.format(config_id)
        all_versions = await self.redis.hgetall(versions_key)
        
        if not all_versions:
            return 1
        
        max_version = max(int(v) for v in all_versions.keys())
        return max_version + 1
    
    async def _store_version(self, config_version: ConfigVersion):
        """Store a configuration version."""
        versions_key = self.versions_key.format(config_version.id)
        
        version_data = {
            "id": config_version.id,
            "version": config_version.version,
            "config_data": config_version.config_data,
            "status": config_version.status.value,
            "created_by": config_version.created_by,
            "created_at": config_version.created_at.isoformat(),
            "description": config_version.description,
            "checksum": config_version.checksum
        }
        
        await self.redis.hset(
            versions_key,
            str(config_version.version),
            json.dumps(version_data)
        )
