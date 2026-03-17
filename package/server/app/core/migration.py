import json
import os.path

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

    logger.info(f"Migrating system config to user {admin_user.username}")

    # Ensure settings is a dict
    if not admin_user.settings:
        admin_user.settings = {}
    config_path = './data/config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        os.remove(config_path)
        admin_user.settings = data

    db.add(admin_user)
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
