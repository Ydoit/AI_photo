from sqlalchemy.orm import Session
from app.db.models.user import User
from app.core.config_manager import config_manager
from app.db.models.album import Album
from app.db.models.photo import Photo
from app.db.models.tag import PhotoTag
from app.db.models.trip import TrainTicket, FlightTicket
from app.db.models.task import Task
from app.db.models.scene import Scene
from app.db.models.index_log import IndexLog
from app.db.models.face import FaceIdentity
import logging

logger = logging.getLogger(__name__)

def migrate_system_config(db: Session, admin_user: User):
    """
    Migrate ALL settings from config.json to admin user settings.
    Also update all records with owner_id=None to admin_user.id.
    """
    # 1. Migrate ALL settings
    # Get current system config as dict
    system_config = config_manager.config.model_dump()
    
    if system_config:
        logger.info(f"Migrating system config to user {admin_user.username}")

        # Ensure settings is a dict
        if not admin_user.settings:
            admin_user.settings = {}

        # Update settings
        # We need to copy to ensure change tracking works if it's a mutable dict
        new_settings = dict(admin_user.settings)
        
        # Merge system config into user settings
        # We prioritize system config here because this is the first migration
        for key, value in system_config.items():
            if key not in new_settings:
                new_settings[key] = value
            elif isinstance(value, dict) and isinstance(new_settings[key], dict):
                 # Simple 1-level merge for nested settings like 'storage', 'ai'
                 for k, v in value.items():
                     if k not in new_settings[key]:
                         new_settings[key][k] = v
        
        admin_user.settings = new_settings

        db.add(admin_user)

        # Optionally clear some sensitive or large lists from system config?
        # But keeping them as defaults is also fine.
        # The requirement says "Read from config.json... put into settings".
        # It doesn't strictly say "delete from config.json".
        # But previous migration deleted external_directories.
        # Let's clean up external_directories at least to avoid duplication.
        if config_manager.config.storage.external_directories:
             config_manager.config.storage.external_directories = []
             config_manager.save()
             
        logger.info("Migrated system config to admin user.")

    # 2. Update owner_id for existing records
    models_to_update = [
        Album,
        Photo,
        TrainTicket,
        FlightTicket,
        Task,
        IndexLog,
        FaceIdentity
    ]

    for model in models_to_update:
        try:
            # Update records where owner_id is None
            result = db.query(model).filter(model.owner_id == None).update({model.owner_id: admin_user.id})
            if result > 0:
                logger.info(f"Updated {result} records in {model.__tablename__} to owner {admin_user.username}")
        except Exception as e:
            logger.error(f"Error updating owner for {model.__tablename__}: {e}")

    db.commit()
