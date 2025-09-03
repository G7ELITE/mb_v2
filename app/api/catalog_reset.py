"""
Catalog Reset API - Safe catalog/procedures reset mechanism
Provides endpoints to reset automation catalogs and procedures safely.
"""
import os
import yaml
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from app.infra.logging import log_structured
from app.core.contexto_lead import get_contexto_lead_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/catalog", tags=["catalog"])

POLICIES_DIR = "policies"
BACKUP_DIR = "backup"

class CatalogResetService:
    """Service for safely resetting catalogs and procedures."""
    
    def __init__(self):
        self.contexto_service = get_contexto_lead_service()
        
    async def create_backup(self, include_database: bool = True) -> str:
        """
        Create backup of current catalog and procedures.
        
        Args:
            include_database: Whether to backup database context data
            
        Returns:
            Backup path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"catalog_backup_{timestamp}")
        
        try:
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup YAML files
            yaml_files = ["catalog.yml", "procedures.yml", "confirm_targets.yml"]
            
            for yaml_file in yaml_files:
                source_path = os.path.join(POLICIES_DIR, yaml_file)
                if os.path.exists(source_path):
                    shutil.copy2(source_path, backup_path)
                    log_structured("info", "catalog_backup_file", {
                        "file": yaml_file,
                        "backup_path": backup_path
                    })
            
            # Create backup info file
            backup_info = {
                "timestamp": timestamp,
                "files_backed_up": yaml_files,
                "include_database": include_database,
                "created_at": datetime.now().isoformat()
            }
            
            with open(os.path.join(backup_path, "backup_info.json"), "w") as f:
                import json
                json.dump(backup_info, f, indent=2)
            
            log_structured("info", "catalog_backup_created", {
                "backup_path": backup_path,
                "files_count": len(yaml_files)
            })
            
            return backup_path
            
        except Exception as e:
            log_structured("error", "catalog_backup_failed", {
                "error": str(e),
                "backup_path": backup_path
            })
            raise
    
    async def reset_catalogs(self, keep_confirm_targets: bool = True) -> Dict[str, Any]:
        """
        Reset catalogs to empty state.
        
        Args:
            keep_confirm_targets: Whether to preserve confirm targets
            
        Returns:
            Reset result summary
        """
        try:
            reset_results = {
                "catalog_reset": False,
                "procedures_reset": False,
                "confirm_targets_preserved": keep_confirm_targets,
                "files_reset": []
            }
            
            # Reset catalog.yml
            catalog_path = os.path.join(POLICIES_DIR, "catalog.yml")
            if os.path.exists(catalog_path):
                empty_catalog = "---\n# Catálogo de Automações - ManyBlack V2 (RESET)\n# Catálogo vazio - criar automações via UI\n\n[]"
                with open(catalog_path, "w", encoding="utf-8") as f:
                    f.write(empty_catalog)
                reset_results["catalog_reset"] = True
                reset_results["files_reset"].append("catalog.yml")
            
            # Reset procedures.yml
            procedures_path = os.path.join(POLICIES_DIR, "procedures.yml")
            if os.path.exists(procedures_path):
                empty_procedures = "---\n# Procedimentos - ManyBlack V2 (RESET)\n# Procedimentos vazios - criar via UI\n\n[]"
                with open(procedures_path, "w", encoding="utf-8") as f:
                    f.write(empty_procedures)
                reset_results["procedures_reset"] = True
                reset_results["files_reset"].append("procedures.yml")
            
            # Clear caches
            await self._clear_caches()
            
            log_structured("info", "catalog_reset_complete", reset_results)
            
            return reset_results
            
        except Exception as e:
            log_structured("error", "catalog_reset_failed", {
                "error": str(e)
            })
            raise
    
    async def _clear_caches(self):
        """Clear all catalog caches."""
        try:
            # Clear automation hook cache
            from app.core.automation_hook import _catalog_cache
            globals()["_catalog_cache"] = None
            
            # Clear selector cache
            from app.core.selector import _CATALOG_CACHE
            globals()["_CATALOG_CACHE"] = None
            
            # Clear procedures cache
            from app.core.procedures import _PROCEDURES_CACHE
            globals()["_PROCEDURES_CACHE"] = None
            
            log_structured("info", "catalog_caches_cleared", {})
            
        except Exception as e:
            logger.warning(f"Error clearing caches: {e}")
    
    async def get_catalog_stats(self) -> Dict[str, Any]:
        """Get current catalog statistics."""
        try:
            stats = {
                "automations_count": 0,
                "procedures_count": 0,
                "confirm_targets_count": 0,
                "catalog_empty": True,
                "procedures_empty": True
            }
            
            # Count automations
            catalog_path = os.path.join(POLICIES_DIR, "catalog.yml")
            if os.path.exists(catalog_path):
                with open(catalog_path, "r", encoding="utf-8") as f:
                    catalog_data = yaml.safe_load(f) or []
                    if isinstance(catalog_data, list):
                        stats["automations_count"] = len(catalog_data)
                        stats["catalog_empty"] = len(catalog_data) == 0
            
            # Count procedures
            procedures_path = os.path.join(POLICIES_DIR, "procedures.yml")
            if os.path.exists(procedures_path):
                with open(procedures_path, "r", encoding="utf-8") as f:
                    procedures_data = yaml.safe_load(f) or []
                    if isinstance(procedures_data, list):
                        stats["procedures_count"] = len(procedures_data)
                        stats["procedures_empty"] = len(procedures_data) == 0
            
            # Count confirm targets
            confirm_targets_path = os.path.join(POLICIES_DIR, "confirm_targets.yml")
            if os.path.exists(confirm_targets_path):
                with open(confirm_targets_path, "r", encoding="utf-8") as f:
                    targets_data = yaml.safe_load(f) or {}
                    if isinstance(targets_data, dict):
                        stats["confirm_targets_count"] = len(targets_data)
            
            return stats
            
        except Exception as e:
            log_structured("error", "catalog_stats_failed", {
                "error": str(e)
            })
            return {"error": str(e)}


# Global service instance
_reset_service = None

def get_reset_service() -> CatalogResetService:
    """Get the catalog reset service instance."""
    global _reset_service
    if _reset_service is None:
        _reset_service = CatalogResetService()
    return _reset_service


@router.get("/stats")
async def get_catalog_stats(service: CatalogResetService = Depends(get_reset_service)):
    """Get catalog statistics."""
    return await service.get_catalog_stats()


@router.post("/backup")
async def create_backup(
    include_database: bool = True,
    service: CatalogResetService = Depends(get_reset_service)
):
    """Create backup of current catalogs."""
    try:
        backup_path = await service.create_backup(include_database)
        return {
            "success": True,
            "backup_path": backup_path,
            "message": "Backup created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/reset")
async def reset_catalogs(
    keep_confirm_targets: bool = True,
    create_backup_first: bool = True,
    service: CatalogResetService = Depends(get_reset_service)
):
    """Reset catalogs to empty state."""
    try:
        backup_path = None
        if create_backup_first:
            backup_path = await service.create_backup(include_database=False)
        
        reset_results = await service.reset_catalogs(keep_confirm_targets)
        
        return {
            "success": True,
            "backup_path": backup_path,
            "reset_results": reset_results,
            "message": "Catalogs reset successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.post("/clear-caches")
async def clear_caches(service: CatalogResetService = Depends(get_reset_service)):
    """Clear all catalog caches."""
    try:
        await service._clear_caches()
        return {
            "success": True,
            "message": "Caches cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.post("/save")
async def save_catalog(
    data: Dict[str, Any],
    service: CatalogResetService = Depends(get_reset_service)
):
    """Save catalog content to YAML file."""
    try:
        content = data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Missing content field")
        
        import yaml
        
        # Validate YAML content first
        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML content: {str(e)}")
        
        # Write to catalog file
        catalog_path = os.path.join(POLICIES_DIR, "catalog.yml")
        with open(catalog_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Clear caches
        await service._clear_caches()
        
        log_structured("info", "catalog_saved", {
            "file": "catalog.yml",
            "items_count": len(parsed_content) if isinstance(parsed_content, list) else 0
        })
        
        return {
            "success": True,
            "message": "Catalog saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_structured("error", "catalog_save_failed", {
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to save catalog: {str(e)}")


@router.post("/save-procedures") 
async def save_procedures(
    data: Dict[str, Any],
    service: CatalogResetService = Depends(get_reset_service)
):
    """Save procedures content to YAML file."""
    try:
        content = data.get("content", "")
        if not content:
            raise HTTPException(status_code=400, detail="Missing content field")
        
        import yaml
        
        # Validate YAML content first
        try:
            parsed_content = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML content: {str(e)}")
        
        # Write to procedures file
        procedures_path = os.path.join(POLICIES_DIR, "procedures.yml")
        with open(procedures_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Clear caches
        await service._clear_caches()
        
        log_structured("info", "procedures_saved", {
            "file": "procedures.yml", 
            "items_count": len(parsed_content) if isinstance(parsed_content, list) else 0
        })
        
        return {
            "success": True,
            "message": "Procedures saved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_structured("error", "procedures_save_failed", {
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to save procedures: {str(e)}")
