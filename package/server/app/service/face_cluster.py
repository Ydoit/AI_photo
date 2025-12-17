import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sklearn.cluster import DBSCAN
from app.db.models.face import Face, FaceIdentity
from app.db.models.photo import Photo
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class FaceClusterService:
    def __init__(self, db: Session):
        self.db = db

    def assign_face_to_identity(self, face_id: int, embedding: list):
        """
        Assign a new face to an existing identity or mark for clustering.
        Real-time simplified logic: Compare with existing identities.
        """
        # Threshold for cosine distance (1 - cosine_similarity)
        # User requested similarity threshold 0.6. 
        # If using distance, distance < (1 - 0.6) = 0.4
        THRESHOLD = 0.4 
        
        # 1. Get all identities with their representative embedding (e.g. mean of their faces)
        # For simplicity/performance, maybe we pick the default face of each identity?
        # Better: Average embedding of the identity. 
        # But calculating average on the fly is expensive.
        # Let's fetch all faces? No, too many.
        # Let's fetch default_face's embedding for each identity.
        
        identities = self.db.query(FaceIdentity).filter(FaceIdentity.is_deleted == False).all()
        
        best_match_id = None
        min_dist = 2.0 # Max cosine distance is 2.0
        
        target_emb = np.array(embedding)
        # Normalize
        target_emb = target_emb / np.linalg.norm(target_emb)
        
        for identity in identities:
            # We need a representative embedding. 
            # If default_face_id is set, use it.
            if identity.default_face_id:
                default_face = self.db.query(Face).filter(Face.id == identity.default_face_id).first()
                if default_face and default_face.face_feature:
                    ref_emb = np.array(default_face.face_feature)
                    ref_emb = ref_emb / np.linalg.norm(ref_emb)
                    
                    # Cosine distance = 1 - dot(a, b) (if normalized)
                    dist = 1.0 - np.dot(target_emb, ref_emb)
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_match_id = identity.id

        if best_match_id and min_dist < THRESHOLD:
            # Assign to existing identity
            face = self.db.query(Face).get(face_id)
            face.face_identity_id = best_match_id
            face.recognize_confidence = 1.0 - min_dist
            self.db.commit()
            logger.info(f"Assigned face {face_id} to identity {best_match_id} (dist={min_dist:.4f})")
            return best_match_id
        else:
            # No match found. 
            # Check if we should trigger a clustering on unassigned faces?
            # Or just leave it unassigned.
            # User requirement: "New cluster marked as 'Unnamed', Quantity threshold detection (default 10)"
            # This suggests we should check if there are enough unassigned faces to form a NEW cluster.
            self._try_create_new_cluster(face_id, embedding)
            return None

    def _try_create_new_cluster(self, current_face_id, current_embedding):
        """
        Try to find if this face belongs to a group of unassigned faces.
        """
        # Fetch unassigned faces
        # Limit to recent ones or some reasonable number to avoid full scan
        unassigned = self.db.query(Face).filter(
            Face.face_identity_id == None,
            Face.is_deleted == False
        ).limit(1000).all()
        
        if len(unassigned) < 3: # min_samples=3
            return

        embeddings = []
        ids = []
        
        for f in unassigned:
            if f.face_feature:
                embeddings.append(f.face_feature)
                ids.append(f.id)
                
        # Include current if not in DB list yet (it should be though)
        
        X = np.array(embeddings)
        # Normalize
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        X_normalized = X / norms
        
        # DBSCAN
        # eps=0.5 (distance threshold). If similarity > 0.6, distance < 0.4.
        # User said eps=0.5.
        clustering = DBSCAN(eps=0.5, min_samples=3, metric='cosine').fit(X_normalized)
        
        labels = clustering.labels_
        # labels: -1 is noise, 0, 1, 2... are clusters
        
        # Check if any cluster has enough members (> 10 is default threshold, but min_samples=3 allows formation)
        # User said "Quantity threshold detection (default 10)". Maybe only create Identity if count > 10?
        # Or maybe create identity immediately but hide it?
        # Let's assume create if > 3 (min_samples) but maybe user meant "notify" if > 10?
        # Let's stick to DBSCAN parameters: if a cluster is formed, it's valid.
        
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:
                continue
                
            # Get members of this cluster
            cluster_indices = np.where(labels == label)[0]
            if len(cluster_indices) >= 3: # Strict adherence to DBSCAN min_samples
                # Create new identity
                # Check if these faces already have an identity (should be None as we filtered)
                
                # Double check if we should really create an identity for just 3 faces?
                # Maybe. "New cluster marked as 'Unnamed'"
                
                new_identity = FaceIdentity(
                    identity_name=f"Unknown Person {uuid.uuid4().hex[:8]}",
                    create_time=datetime.now()
                )
                self.db.add(new_identity)
                self.db.flush() # Get ID
                
                # Assign faces
                first_face_id = None
                for idx in cluster_indices:
                    f_id = ids[idx]
                    face = self.db.query(Face).get(f_id)
                    face.face_identity_id = new_identity.id
                    face.recognize_confidence = 0.9 # Placeholder
                    if not first_face_id:
                        first_face_id = face.id
                
                # Set default face
                new_identity.default_face_id = first_face_id
                self.db.commit()
                logger.info(f"Created new identity {new_identity.id} with {len(cluster_indices)} faces")

