
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models.task import Task, TaskStatus
from app.db.models.photo import Photo
from app.service.similar_photo import SimilarPhotoService
import time
import json
from datetime import datetime, timedelta
import numpy as np

# Re-implementing the core logic here to support progress tracking and time-window optimization
# Or we can update SimilarPhotoService to support it.
# Let's update SimilarPhotoService first or inline the optimized logic here.

async def handle_similar_task(worker, task: Task, db: Session):
    """
    Handle similar photo clustering task
    """
    try:
        user_id = str(task.owner_id)
        threshold = task.payload.get('threshold', 0.9)
        time_window = task.payload.get('time_window', 3600) # Default 1 hour window for splitting?
        # Actually, let's use a smaller gap for segmentation, e.g., 10 minutes.
        # If two photos are > 10 mins apart, they are likely not "similar" in the sense of burst shots.
        # But user might want to find duplicates across folders.
        # If across folders/times (exact duplicates), time window might hurt.
        # But for "similar photos" (bursts), time window is key.
        # Let's assume the user intent is primarily "burst cleanup".
        # If user wants "duplicate cleanup", that's usually hash-based or exact match.
        # The prompt says "Similar Photo Cleanup", usually implies bursts.
        
        # However, to be safe, maybe we process all? 
        # But for optimization, let's sort by time and segment.
        
        logging.info(f"Starting similar photo clustering for user {user_id}, threshold={threshold}")
        
        # 1. Fetch all photos with embeddings
        # We need efficient fetching.
        from app.db.models.image_vector import ImageVector
        
        # Fetch ID, Time, Embedding
        stmt = (
            select(ImageVector.photo_id, ImageVector.embedding, Photo.photo_time)
            .join(Photo, ImageVector.photo_id == Photo.id)
            .where(Photo.owner_id == user_id)
            .order_by(Photo.photo_time.asc()) # Sort by time is crucial for windowing
        )
        
        # This might be heavy if we load all embeddings into memory.
        # 512 floats = 2KB. 10000 photos = 20MB. 100k photos = 200MB.
        # Python overhead might make it 1GB+. 
        # It is acceptable for < 100k photos.
        
        results = db.execute(stmt).all()
        total_photos = len(results)
        
        if total_photos == 0:
            task.result = []
            task.status = TaskStatus.COMPLETED
            task.processed_items = 0
            task.total_items = 0
            db.commit()
            return {'status': 'completed', 'count': 0}

        task.total_items = total_photos
        task.processed_items = 0
        db.commit()

        # 2. Segment photos based on time gap
        # If gap > 5 minutes (300s), start new segment.
        GAP_THRESHOLD = 300 
        
        segments = []
        current_segment = []
        last_time = None
        
        for r in results:
            pid = str(r.photo_id)
            embedding = np.array(r.embedding)
            # Handle null photo_time (put them in one segment or separate?)
            # If null, maybe put at the end?
            p_time = r.photo_time
            
            if p_time is None:
                # Treat as separate segment or handle separately? 
                # For now, let's just skip time check for None and put them in a "No Time" segment?
                # Or just treat as 0 timestamp.
                ts = 0
            else:
                ts = p_time.timestamp()
            
            if last_time is None:
                current_segment.append({'id': pid, 'vec': embedding, 'time': ts})
            else:
                if abs(ts - last_time) > GAP_THRESHOLD and ts != 0 and last_time != 0:
                    segments.append(current_segment)
                    current_segment = []
                current_segment.append({'id': pid, 'vec': embedding, 'time': ts})
            
            if ts != 0:
                last_time = ts
        
        if current_segment:
            segments.append(current_segment)
            
        logging.info(f"Split {total_photos} photos into {len(segments)} segments for clustering")
        
        # 3. Process each segment
        from sklearn.cluster import AgglomerativeClustering
        
        all_groups = []
        processed_count = 0
        
        for segment in segments:
            if len(segment) < 2:
                processed_count += len(segment)
                continue
                
            # Prepare data
            X = np.array([item['vec'] for item in segment])
            ids = [item['id'] for item in segment]
            
            # Normalize
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1
            X_normalized = X / norms
            
            # Cluster
            distance_threshold = 1 - threshold
            clustering = AgglomerativeClustering(
                n_clusters=None,
                metric='cosine',
                linkage='average',
                distance_threshold=distance_threshold
            )
            labels = clustering.fit_predict(X_normalized)
            
            # Group locally
            local_groups = {}
            for pid, label in zip(ids, labels):
                if label not in local_groups:
                    local_groups[label] = []
                local_groups[label].append(pid)
            
            # Collect groups with > 1 item
            for p_ids in local_groups.values():
                if len(p_ids) > 1:
                    all_groups.append(p_ids)
            
            processed_count += len(segment)
            
            # Update progress periodically
            if processed_count % 100 == 0:
                task.processed_items = processed_count
                db.commit()
                
        # 4. Fetch details for groups and format result
        # To avoid saving huge JSON, we can format minimal info or full info.
        # User wants "result persistence".
        # Let's use the SimilarPhotoService's formatting logic but adapted.
        
        formatted_groups = []
        
        # Fetch details in batches or all at once?
        # All group photos IDs
        all_group_photo_ids = [pid for group in all_groups for pid in group]
        
        if all_group_photo_ids:
            # Fetch details
            # We need Photo and ImageDescription
            from app.db.models.image_description import ImageDescription
            
            # Fetch all involved photos
            # Chunking if too many
            chunk_size = 500
            photo_details_map = {}
            
            for i in range(0, len(all_group_photo_ids), chunk_size):
                chunk_ids = all_group_photo_ids[i:i+chunk_size]
                detail_stmt = (
                    select(Photo, ImageDescription)
                    .outerjoin(ImageDescription, Photo.id == ImageDescription.photo_id)
                    .where(Photo.id.in_(chunk_ids))
                )
                details = db.execute(detail_stmt).all()
                for photo, desc in details:
                    score = 0
                    if desc:
                        score = (desc.memory_score or 0) + (desc.quality_score or 0)
                    
                    photo_details_map[str(photo.id)] = {
                        "id": str(photo.id),
                        "filename": photo.filename,
                        "photo_time": photo.photo_time.isoformat() if photo.photo_time else None,
                        "score": score,
                        "thumbnail_path": f"/api/medias/{photo.id}/thumbnail",
                        "src": f"/api/medias/{photo.id}/preview"
                    }

            # Construct groups
            for p_ids in all_groups:
                group_items = []
                for pid in p_ids:
                    if pid in photo_details_map:
                        group_items.append(photo_details_map[pid])
                
                # Sort: Score desc, then Photo Time desc
                # Handle None time
                group_items.sort(key=lambda x: (x['score'], x['photo_time'] or ""), reverse=True)
                formatted_groups.append(group_items)

        # Save result
        task.result = formatted_groups
        task.status = TaskStatus.COMPLETED
        task.processed_items = total_photos
        db.commit()
        
        return {'status': 'completed', 'groups': len(formatted_groups)}

    except Exception as e:
        logging.error(f"Similar task failed: {e}")
        task.status = TaskStatus.FAILED
        task.error = str(e)
        db.commit()
        raise e
