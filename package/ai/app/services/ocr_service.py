from paddleocr import PaddleOCR
import numpy as np
import cv2
import logging
from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

def load_paddleocr_model():
    try:
        # use_angle_cls=True loads the angle classifier
        # lang='ch' supports Chinese and English
        # use_gpu will be auto-detected or we can configure it.
        # PaddleOCR handles its own loading.
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            show_log=False,
            device='gpu'
        )
        logger.info("PaddleOCR model initialized successfully.")
        return ocr
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR model: {e}")
        raise e

# Register
model_manager.register_model("ocr", load_paddleocr_model)

class OCRService:
    def __init__(self):
        pass

    def detect_text(self, image_bytes: bytes):
        """
        Detect text in image bytes
        """
        ocr = model_manager.get_model("ocr")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid image data")
            
        # PaddleOCR.ocr takes numpy array (H, W, C)
        # result is a list of lines
        # each line: [ [ [x1,y1], [x2,y2], [x3,y3], [x4,y4] ],  (text, confidence) ]
        result = ocr.ocr(img, cls=True)
        
        parsed_results = []
        # result can be None if nothing found, or list of lists
        if result and result[0]:
            for line in result[0]:
                box = line[0]
                text, score = line[1]
                parsed_results.append({
                    "box": box,
                    "text": text,
                    "score": float(score)
                })
                
        return parsed_results

ocr_service = OCRService()
