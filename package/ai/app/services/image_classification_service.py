from PIL import Image
from app.services.model_manager import model_manager
import logging
import io
import json
import os
from typing import List, Dict, Optional

class CLIPWrapper:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        import torch
        from transformers import CLIPProcessor, CLIPModel
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Loading CLIP model {model_name} on {self.device}")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)

class ImageClassificationService:
    def __init__(self):
        self.model_name = "openai/clip-vit-base-patch32"
        self._register_model()
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "categories.json")
        self.categories: Dict = {}
        self.category_keys: List[str] = []
        self.simple_prompts: List[str] = []
        self._load_categories()

    def _load_model(self):
        return CLIPWrapper(self.model_name)

    def _release_model(self, wrapper):
        """Release resources associated with the model"""
        logging.info(f"Releasing resources for {self.model_name}")
        if hasattr(wrapper, 'model'):
            del wrapper.model
        if hasattr(wrapper, 'processor'):
            del wrapper.processor
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def _register_model(self):
        model_manager.register_model("clip", self._load_model, self._release_model)

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

    async def classify(self, image_data: bytes, lang: str = "zh", limit: int = 3, precision: str = "high") -> list[dict]:
        if not self.categories:
            return []
        import torch
        wrapper = model_manager.get_model("clip")
        try:
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            
            # Determine prompts based on precision
            if precision == "normal":
                # Use pre-calculated simple prompts (first one only)
                text_inputs = self.simple_prompts
                
                inputs = wrapper.processor(
                    text=text_inputs, 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                ).to(wrapper.device)

                with torch.no_grad():
                    outputs = wrapper.model(**inputs)
                
                # Use softmax to get probabilities
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
                
            else: # precision == "high" (default)
                # Use all prompts for each category and average the features/logits
                # This is more computationally expensive but potentially more accurate
                
                # We need to flatten all prompts but keep track of which category they belong to
                all_prompts = []
                prompt_category_map = [] # stores index of category for each prompt
                
                for i, key in enumerate(self.category_keys):
                    prompts = self.categories[key].get("prompts", [])
                    if not prompts:
                        prompts = [f"a photo of {self.categories[key].get('en', key)}"]
                    
                    for p in prompts:
                        all_prompts.append(p)
                        prompt_category_map.append(i)
                
                # Process in batches if too many prompts? 
                # For now assume reasonable number of total prompts (<100)
                inputs = wrapper.processor(
                    text=all_prompts, 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                ).to(wrapper.device)

                with torch.no_grad():
                    outputs = wrapper.model(**inputs)
                
                logits_per_image = outputs.logits_per_image # [1, num_all_prompts]
                
                # Now we need to aggregate logits/probs per category
                # Strategy: average logits per category then softmax? OR softmax then average probs?
                # Usually averaging logits (before softmax) or features is better for CLIP ensembles.
                # Let's average logits per category.
                
                logits = logits_per_image[0] # [num_all_prompts]
                
                # Initialize category logits
                category_logits = torch.zeros(len(self.category_keys), device=wrapper.device)
                category_counts = torch.zeros(len(self.category_keys), device=wrapper.device)
                
                # Map back using prompt_category_map
                # This can be vectorized but loop is fine for small N
                for prompt_idx, cat_idx in enumerate(prompt_category_map):
                    category_logits[cat_idx] += logits[prompt_idx]
                    category_counts[cat_idx] += 1
                
                # Average
                category_logits = category_logits / category_counts
                
                # Softmax
                probs = category_logits.softmax(dim=0).cpu().numpy()

            # Create result list
            results = []
            for i, score in enumerate(probs):
                key = self.category_keys[i]
                category_info = self.categories[key]
                label = category_info.get(lang, category_info["zh"]) # Default to zh if lang not found
                results.append({
                    "category": key, # Internal key
                    "label": label,  # Display label
                    "confidence": float(score)
                })
            
            # Sort by confidence desc
            results.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Return top N
            return results[:limit]
            
        except Exception as e:
            logging.error(f"Error in image classification: {e}")
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
