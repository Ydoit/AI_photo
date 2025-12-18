import numpy as np
import cv2
import insightface
from insightface.app import FaceAnalysis
from app.config import settings
import logging
import onnxruntime as ort
from app.services.model_manager import model_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_insightface_model():
    try:
        # Initialize InsightFace analysis
        # providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if GPU available
        provider_options = [{"device_id": 0}, {}]
        app = FaceAnalysis(
            name='buffalo_l', root=settings.INSIGHTFACE_MODEL_PATH,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
            provider_options = provider_options  # 传递 CUDA 配置
        )
        app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace model initialized successfully.")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize InsightFace model: {e}")
        raise e

# Register the model
model_manager.register_model("face", load_insightface_model)

class FaceRecognitionService:
    def __init__(self):
        # Model loading is delegated to ModelManager
        pass

    def process_image(self, image_bytes: bytes):
        """
        Process image bytes and return face analysis results
        """
        # Get model instance from manager (lazy load if needed)
        app = model_manager.get_model("face")
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")

        # Perform face analysis
        faces = app.get(img)
        
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
