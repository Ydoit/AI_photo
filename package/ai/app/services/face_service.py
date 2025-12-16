import numpy as np
import cv2
import insightface
from insightface.app import FaceAnalysis
from app.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognitionService:
    def __init__(self):
        self.app = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            # Initialize InsightFace analysis
            # providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if GPU available
            self.app = FaceAnalysis(name='buffalo_l', root=settings.INSIGHTFACE_MODEL_PATH)
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace model: {e}")
            raise e

    def process_image(self, image_bytes: bytes):
        """
        Process image bytes and return face analysis results
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")

        # Perform face analysis
        faces = self.app.get(img)
        
        results = []
        for face in faces:
            # Extract relevant data
            # face.bbox is [x1, y1, x2, y2]
            # face.kps is 5 keypoints (eyes, nose, mouth corners)
            # face.embedding is 512-d feature vector
            # face.det_score is detection confidence
            
            face_data = {
                "bbox": face.bbox.tolist(),
                "kps": face.kps.tolist(),
                "det_score": float(face.det_score),
                "embedding": face.embedding.tolist(), # Convert numpy array to list for JSON serialization
                # "gender": face.sex, # Available in some models
                # "age": face.age,    # Available in some models
            }
            results.append(face_data)
            
        return results

# Singleton instance
face_service = FaceRecognitionService()
