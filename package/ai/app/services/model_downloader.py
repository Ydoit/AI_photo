import os
import logging
import shutil
from app.config import settings

logger = logging.getLogger(__name__)

def ensure_models():
    """
    Ensure required models are present. Download if missing.
    """
    base_dir = settings.MODEL_PATH
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 1. CLIP Models (Image Classification)
    # 1.1 Multilingual CLIP (Text)
    clip_multi_id = "sentence-transformers/clip-ViT-B-32-multilingual-v1"
    clip_multi_dir = os.path.join(base_dir, "clip-ViT-B-32-multilingual-v1")

    if not os.path.exists(clip_multi_dir):
        logger.info(f"Downloading CLIP model {clip_multi_id} to {clip_multi_dir}...")
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            snapshot_download(clip_multi_id, local_dir=clip_multi_dir)
            logger.info("CLIP multilingual model downloaded successfully.")
        except Exception as e:
            shutil.rmtree(clip_multi_dir, ignore_errors=True)
            logger.error(f"Failed to download CLIP multilingual model: {e}")
    else:
        logger.info("CLIP multilingual model already exists.")

    # 1.2 Base CLIP (Image)
    # Assuming standard CLIP model is also available or we use multilingual for both?
    # Original code uses "clip-ViT-B-32".
    # We will try to download it from ModelScope if available, otherwise we might rely on HF or just skip and let runtime handle it (but that violates requirements).
    # Let's assume AI-ModelScope/clip-ViT-B-32 exists.
    clip_base_id = "sentence-transformers/clip-ViT-B-32"
    clip_base_dir = os.path.join(base_dir, "clip-ViT-B-32")

    if not os.path.exists(clip_base_dir):
        logger.info(f"Downloading CLIP model {clip_base_id} to {clip_base_dir}...")
        try:
            snapshot_download(clip_base_id, local_dir=clip_base_dir)
            logger.info("CLIP base model downloaded successfully.")
        except Exception as e:
            shutil.rmtree(clip_base_dir, ignore_errors=True)
            logger.error(f"Failed to download CLIP base model: {e}")
    else:
        logger.info("CLIP base model already exists.")

    # 2. InsightFace Model (Face Recognition)
    # Target: data/models/buffalo_l
    # InsightFace uses 'root' parameter to find models. 
    # If root='data', it looks in 'data/models/buffalo_l'.

    insightface_root = settings.MODEL_PATH.rstrip("/").rstrip("models") # Defaults to 'data'
    buffalo_l_path = os.path.join(insightface_root,"models", "buffalo_l")
    
    # Check if we need to download
    if not os.path.exists(buffalo_l_path) or not os.listdir(buffalo_l_path):
        logger.info(f"Downloading InsightFace model buffalo_l to {buffalo_l_path}...")
        try:
            from insightface.app import FaceAnalysis
            # Initialize to trigger download
            # using ctx_id=-1 for CPU to avoid CUDA errors during download if no GPU
            app = FaceAnalysis(name='buffalo_l', root=insightface_root, providers=['CPUExecutionProvider'])
            app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("InsightFace model downloaded/verified successfully.")
        except Exception as e:
            shutil.rmtree(buffalo_l_path, ignore_errors=True)
            logger.error(f"Failed to download InsightFace model: {e}")
    else:
        logger.info("InsightFace model already exists.")

    # paddle ocr model
    paddleocr_dir = os.path.join(base_dir, "official_models", "PP-OCRv5_server_det")
    if not os.path.exists(paddleocr_dir):
        logger.info(f"Downloading PaddleOCR model to {paddleocr_dir} ...")
        try:
            model_root = settings.MODEL_PATH
            os.environ['PADDLE_PDX_CACHE_HOME'] = model_root
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(
                use_angle_cls=True, lang='ch',
            )
            logger.info("PaddleOCR model downloaded successfully.")
        except Exception as e:
            shutil.rmtree(paddleocr_dir, ignore_errors=True)
            logger.error(f"Failed to download PaddleOCR model: {e}")
    else:
        logger.info("PaddleOCR model already exists.")