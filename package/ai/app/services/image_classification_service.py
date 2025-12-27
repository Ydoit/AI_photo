import traceback

from PIL import Image

from app.config import settings
from app.services.model_downloader import model_downloader
from app.services.model_manager import model_manager
from app.services.ai_config_manager import ai_config_manager
import logging
import io
import json
import os
from typing import List, Dict, Optional

class SentenceTransformerWrapper:
    def __init__(self, model_name="sentence-transformers/clip-ViT-B-32-multilingual-v1"):
        from sentence_transformers import SentenceTransformer
        import torch
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Loading SentenceTransformer model {model_name} on {self.device}")
        self.model = SentenceTransformer(model_name, device=self.device, cache_folder=settings.MODEL_PATH)

class ImageClassificationService:
    def __init__(self):
        self._register_models()
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "categories.json")
        self.categories: Dict = {}
        self.category_keys: List[str] = []
        self.simple_prompts: List[str] = []
        self._load_categories()
        self._register_downloads()

    def _get_model_info(self):
        selected = ai_config_manager.get_model_selection("classification")
        # Map selection to actual model repos/paths
        # This could also be in config, but hardcoding the logic here for now as "Global Variables" equivalent
        if selected == "clip-ViT-B-32":
            return {
                "text_model_repo": "sentence-transformers/clip-ViT-B-32-multilingual-v1",
                "image_model_repo": "sentence-transformers/clip-ViT-B-32",
                "text_dir_name": "clip-ViT-B-32-multilingual-v1",
                "image_dir_name": "clip-ViT-B-32"
            }
        return {
                "text_model_repo": "sentence-transformers/clip-ViT-B-32-multilingual-v1",
                "image_model_repo": "sentence-transformers/clip-ViT-B-32",
                "text_dir_name": "clip-ViT-B-32-multilingual-v1",
                "image_dir_name": "clip-ViT-B-32"
        }

    def _register_downloads(self):
        
        def check_image_model():
            info = self._get_model_info()
            path = os.path.join(settings.MODEL_PATH, info["image_dir_name"])
            return os.path.exists(path) and len(os.listdir(path)) > 0

        def download_image_model():
            info = self._get_model_info()
            path = os.path.join(settings.MODEL_PATH, info["image_dir_name"])
            from modelscope.hub.snapshot_download import snapshot_download
            logging.info(f"Downloading Image model {info['image_model_repo']} to {path}...")
            return snapshot_download(info['image_model_repo'], local_dir=path)

        def check_text_model():
            info = self._get_model_info()
            path = os.path.join(settings.MODEL_PATH, info["text_dir_name"])
            return os.path.exists(path) and len(os.listdir(path)) > 0

        def download_text_model():
            info = self._get_model_info()
            path = os.path.join(settings.MODEL_PATH, info["text_dir_name"])
            from modelscope.hub.snapshot_download import snapshot_download
            logging.info(f"Downloading Text model {info['text_model_repo']} to {path}...")
            return snapshot_download(info['text_model_repo'], local_dir=path)

        model_downloader.register_model("clip_text", check_text_model, download_text_model)
        model_downloader.register_model("clip_image", check_image_model, download_image_model)

    def _load_text_model(self):
        info = self._get_model_info()
        path = os.path.join(settings.MODEL_PATH, info["text_dir_name"])
        # If not exists (should be handled by downloader), fallback to repo name which might auto-download by sentence-transformers
        model_name = path if os.path.exists(path) else info["text_model_repo"]
        return SentenceTransformerWrapper(model_name)

    def _load_image_model(self):
        info = self._get_model_info()
        path = os.path.join(settings.MODEL_PATH, info["image_dir_name"])
        model_name = path if os.path.exists(path) else info["image_model_repo"]
        return SentenceTransformerWrapper(model_name)

    def _release_model(self, wrapper):
        """Release resources associated with the model"""
        model_name = getattr(wrapper, 'model_name', 'unknown')
        logging.info(f"Releasing resources for {model_name}")
        if hasattr(wrapper, 'model'):
            del wrapper.model
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _register_models(self):
        model_manager.register_model("clip_text", self._load_text_model, self._release_model)
        model_manager.register_model("clip_image", self._load_image_model, self._release_model)

    def _load_categories(self):
        """Load categories from JSON file"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.categories = json.load(f)
            else:
                logging.warning(f"Categories file not found at {self.data_path}, using empty categories.")
                self.categories = {}
            self._update_internal_structures()
            logging.info(f"Loaded {len(self.categories)} categories from {self.data_path}")
        except Exception as e:
            logging.error(f"Failed to load categories: {e}")
            # Fallback or empty? keeping empty for now
            self.categories = {}
            self._update_internal_structures()

    def _save_categories(self):
        """Save current categories to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
            logging.info(f"Saved categories to {self.data_path}")
            self._update_internal_structures()
        except Exception as e:
            logging.error(f"Failed to save categories: {e}")
            raise e

    def _update_internal_structures(self):
        """Update helper lists based on current categories"""
        self.category_keys = list(self.categories.keys())
        # Use the first prompt as the representative prompt for CLIP
        self.simple_prompts = []
        for key in self.category_keys:
            prompts = self.categories[key].get("prompts", [])
            if prompts:
                self.simple_prompts.append(prompts[0])
            else:
                # Fallback prompt if list is empty
                self.simple_prompts.append(f"a photo of {self.categories[key].get('en', key)}")

    async def classify(self, image_data: bytes, lang: str = "zh", limit: int = 3, precision: str = "high") -> dict:
        if not model_downloader.is_ready("clip_text") or not model_downloader.is_ready("clip_image"):
            raise Exception("Models are not ready yet. Please try again later.")

        if not self.categories:
            return {"results": [], "embedding": []}
        import torch
        from sentence_transformers import util
        
        # Get models
        text_wrapper = model_manager.get_model("clip_text")
        image_wrapper = model_manager.get_model("clip_image")

        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            
            # Encode image using image model
            # convert_to_tensor=True to keep it on device if possible
            image_emb = image_wrapper.model.encode(image, convert_to_tensor=True)
            
            # Determine prompts based on precision
            if precision == "normal":
                text_inputs = self.simple_prompts
                text_embs = text_wrapper.model.encode(text_inputs, convert_to_tensor=True)
                
                if image_emb.device != text_embs.device:
                    text_embs = text_embs.to(image_emb.device)

                # Compute cosine similarity
                cos_scores = util.cos_sim(image_emb, text_embs)[0]
                
            else: # precision == "high" (default)
                all_prompts = []
                prompt_category_map = [] 
                
                for i, key in enumerate(self.category_keys):
                    prompts = self.categories[key].get("prompts", [])
                    if not prompts:
                        prompts = [f"a photo of {self.categories[key].get('en', key)}"]
                    
                    for p in prompts:
                        all_prompts.append(p)
                        prompt_category_map.append(i)
                
                text_embs = text_wrapper.model.encode(all_prompts, convert_to_tensor=True)
                
                # Aggregate embeddings per category
                category_embs = torch.zeros((len(self.category_keys), text_embs.shape[1]), device=image_emb.device)
                category_counts = torch.zeros(len(self.category_keys), device=image_emb.device)
                
                # Ensure text_embs is on same device for aggregation if needed, or aggregate on its device then move?
                # Simpler: move text_embs to image_emb device (which is where category_embs is)
                if text_embs.device != image_emb.device:
                    text_embs = text_embs.to(image_emb.device)

                for prompt_idx, cat_idx in enumerate(prompt_category_map):
                    category_embs[cat_idx] += text_embs[prompt_idx]
                    category_counts[cat_idx] += 1
                
                # Average
                category_embs = category_embs / category_counts.unsqueeze(1)
                
                # Compute cosine similarity
                cos_scores = util.cos_sim(image_emb, category_embs)[0]

            # Convert to probabilities (softmax)
            scores = cos_scores * 100
            probs = scores.softmax(dim=0).cpu().numpy()

            # Create result list
            results = []
            for i, score in enumerate(probs):
                key = self.category_keys[i]
                category_info = self.categories[key]
                label = category_info.get(lang, category_info["zh"]) 
                results.append({
                    "category": key, 
                    "label": label, 
                    "confidence": float(score)
                })
            
            # Sort by confidence desc
            results.sort(key=lambda x: x["confidence"], reverse=True)
            
            return {
                "results": results[:limit],
                "embedding": image_emb.cpu().tolist()
            }
            
        except Exception as e:
            logging.error(f"Error in image classification: {e}")
            raise e

    async def embed_text(self, text: str) -> List[float]:
        if not model_downloader.is_ready("clip_text"):
             raise Exception("Models are not ready yet. Please try again later.")
        wrapper = model_manager.get_model("clip_text")
        try:
            # Encode text
            text_emb = wrapper.model.encode(text, convert_to_tensor=False)
            return text_emb.tolist()
        except Exception as e:
            logging.error(f"Error in text embedding: {e}\n{traceback.format_exc()}")
            raise e

    # --- Management Methods ---

    def get_categories(self) -> Dict:
        return self.categories

    def add_category(self, key: str, zh: str, en: str, prompts: List[str]):
        if key in self.categories:
            raise ValueError(f"Category '{key}' already exists.")
        
        self.categories[key] = {
            "zh": zh,
            "en": en,
            "prompts": prompts
        }
        self._save_categories()

    def update_category(self, key: str, zh: Optional[str] = None, en: Optional[str] = None, prompts: Optional[List[str]] = None):
        if key not in self.categories:
            raise ValueError(f"Category '{key}' not found.")
        
        if zh:
            self.categories[key]["zh"] = zh
        if en:
            self.categories[key]["en"] = en
        if prompts is not None:
            self.categories[key]["prompts"] = prompts
            
        self._save_categories()

    def delete_category(self, key: str):
        if key not in self.categories:
            raise ValueError(f"Category '{key}' not found.")
        
        del self.categories[key]
        self._save_categories()

image_classification_service = ImageClassificationService()
