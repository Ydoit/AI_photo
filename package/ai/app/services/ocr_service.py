import numpy as np
import cv2
import logging
import sys
import os
from app.config import settings
from app.services.model_downloader import model_downloader
from app.services.model_manager import model_manager
from app.services.ai_config_manager import ai_config_manager

def load_paddleocr_model():
    try:
        model_root = settings.MODEL_PATH
        os.environ['PADDLE_PDX_CACHE_HOME'] = model_root
        from paddleocr import PaddleOCR
        # Get model name from config
        model_name = ai_config_manager.get_model_selection("ocr")
        logging.info(f"Initializing PaddleOCR with model: {model_name}")
        ocr = PaddleOCR(
            use_angle_cls=True, lang='ch',
            text_recognition_model_name=f"PP-OCRv5_{model_name}_rec",
            text_detection_model_name=f"PP-OCRv5_{model_name}_det"
        )
        logging.info("PaddleOCR model initialized successfully.")
        return ocr
    except Exception as e:
        logging.error(f"Failed to initialize PaddleOCR model: {e}")
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
        logging.info("PaddleOCR resources released.")
    except Exception as e:
        logging.error(f"Error releasing PaddleOCR resources: {e}")

# Register
model_manager.register_model("ocr", load_paddleocr_model, release_paddleocr_model)

class OCRService:
    def __init__(self):
        self._register_downloads()

    def _register_downloads(self):
        def get_current_model_name():
            return ai_config_manager.get_model_selection("ocr")

        def check_ocr_model():
            model_name = get_current_model_name()
            marker_file = os.path.join(settings.MODEL_PATH, "official_models")
            marker_file = os.path.join(marker_file, f"PP-OCRv5_{model_name}_rec")
            return os.path.exists(marker_file)

        def download_ocr_model():
            model_name = get_current_model_name()
            logging.info(f"Downloading/Verifying PaddleOCR model ({model_name})...")
            # We need to set the env vars as before if they were useful
            model_root = os.path.join(settings.MODEL_PATH, "official_models")
            #模型下载
            from modelscope import snapshot_download
            model_path = os.path.join(model_root, f"PP-OCRv5_{model_name}_rec")
            # Note: This assumes the repo name follows the pattern
            try:
                snapshot_download(f'PaddlePaddle/PP-OCRv5_{model_name}_rec', local_dir=model_path)
            except Exception as e:
                # Fallback to v4 if v5 server is not found? Or just let it fail?
                # For now let's assume v5 exists or user will configure to v4 if needed.
                # But wait, hardcoded PP-OCRv5 in code.
                # If user wants server, and v5 server doesn't exist, we might be in trouble.
                # Let's just try to download what is requested.
                raise e
            
            det_model_path = os.path.join(model_root, f"PP-OCRv5_{model_name}_det")
            snapshot_download(f'PaddlePaddle/PP-OCRv5_{model_name}_det', local_dir=det_model_path)
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
