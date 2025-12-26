import numpy as np
import cv2
import logging
import sys
import os
from app.config import settings
from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

def load_paddleocr_model():
    try:
        model_root = settings.MODEL_PATH
        os.environ['PADDLE_PDX_CACHE_HOME'] = model_root
        from paddleocr import PaddleOCR
        # use_angle_cls=True loads the angle classifier
        # lang='ch' supports Chinese and English
        # use_gpu will be auto-detected or we can configure it.
        # PaddleOCR handles its own loading.
        # We can pass `use_gpu=True` if we want to enforce it, but Paddle usually auto-detects.
        # 核心：设置PADDLEX_HOME，指定模型默认下载到data/models
        # 优先用绝对路径（推荐），也可用相对路径

        ocr = PaddleOCR(
            use_angle_cls=True, lang='ch',
        )
        logger.info("PaddleOCR model initialized successfully.")
        return ocr
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR model: {e}")
        raise e

def release_paddleocr_model(model):
    try:
        # PaddleOCR doesn't have an explicit close/release method for the object itself easily exposed
        # But we can try to unload modules if we want to go extreme, though dangerous in async env.
        # Generally, just deleting the object and gc.collect() (handled by wrapper) is enough for object memory.
        # To clear GPU cache for Paddle:
        import paddle
        if paddle.is_compiled_with_cuda():
            paddle.device.cuda.empty_cache()

        # Optional: Unload heavy modules if they were lazy imported and we want to reclaim code memory?
        # Typically not recommended to unload modules in Python servers as re-importing is tricky.
        # But user asked to "clean import modules".
        # We can try to remove 'paddleocr' and 'paddle' from sys.modules if we are sure no one else uses it.
        # WARNING: This is risky if other threads are using it or if re-import fails.
        # A safer approach is just releasing GPU memory.

        # Let's stick to GPU cache clearing and object deletion first. 
        # If user explicitly wants module unloading:
        # modules_to_unload = [m for m in sys.modules if m.startswith('paddle')]
        # for m in modules_to_unload:
        #     del sys.modules[m]
        # This is often too aggressive and causes crashes. 
        # We will focus on the resource release hook.
        logger.info("PaddleOCR resources released.")
    except Exception as e:
        logger.error(f"Error releasing PaddleOCR resources: {e}")

# Register
model_manager.register_model("ocr", load_paddleocr_model, release_paddleocr_model)

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

        results = ocr.ocr(img)

        parsed_results = []
        for res in results:
            parsed_results.append(
                {
                    "prunedResult": res.json['res'],

                }
            )
        return parsed_results

ocr_service = OCRService()
