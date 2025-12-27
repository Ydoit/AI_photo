import numpy as np
import cv2
import logging
import sys
import os
from app.config import settings
from app.services.model_downloader import model_downloader
from app.services.model_manager import model_manager

logger = logging.getLogger(__name__)

def load_paddleocr_model():
    try:
        model_root = settings.MODEL_PATH
        os.environ['PADDLE_PDX_CACHE_HOME'] = model_root
        from paddleocr import PaddleOCR
        # 优先用绝对路径（推荐），也可用相对路径
        model_name = 'mobile'
        ocr = PaddleOCR(
            use_angle_cls=True, lang='ch',
            text_recognition_model_name=f"PP-OCRv5_{model_name}_rec",
            text_detection_model_name=f"PP-OCRv5_{model_name}_det"
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
    def __init__(self, model_name="mobile"):
        self.model_name = model_name
        self._register_downloads()

    def _register_downloads(self):
        marker_file = os.path.join(settings.MODEL_PATH, "official_models")
        marker_file = os.path.join(marker_file, f"PP-OCRv5_{self.model_name}_rec")
        def check_ocr_model():
            return os.path.exists(marker_file)

        def download_ocr_model():
            logger.info(f"Downloading/Verifying PaddleOCR model...")
            # We need to set the env vars as before if they were useful
            model_root = os.path.join(settings.MODEL_PATH, "official_models")
            #模型下载
            from modelscope import snapshot_download
            model_path = os.path.join(model_root, f"PP-OCRv5_{self.model_name}_rec")
            model_dir = snapshot_download(f'PaddlePaddle/PP-OCRv5_{self.model_name}_rec', local_dir=model_path)
            model_path = os.path.join(model_root, f"PP-OCRv5_{self.model_name}_det")
            model_dir = snapshot_download(f'PaddlePaddle/PP-OCRv5_{self.model_name}_det', local_dir=model_path)
            return model_path
        model_downloader.register_model("ocr", check_ocr_model, download_ocr_model)


    def detect_text(self, image_bytes: bytes):
        """
        Detect text in image bytes
        """
        if not model_downloader.is_ready("ocr"):
             raise Exception("OCR model is not ready yet. Please try again later.")

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
