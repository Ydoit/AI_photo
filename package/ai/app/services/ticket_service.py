import uuid
import json
import tempfile
import numpy as np
import cv2
import logging
import os
from app.config import settings
from app.services.model_manager import model_manager
from app.services.ticket_parser import parse_ticket_info, extract_text
from ultralytics import YOLO

def load_yolo_model():
    try:
        # 优先查找配置的AI模型目录
        model_path = os.path.join(settings.MODEL_PATH, "tickets", "best.pt")
        
        # 如果不存在，尝试使用开发环境中的原始路径
        if not os.path.exists(model_path):
            # 硬编码回退路径，指向 server/yolo_ocr/best.pt
            # 假设当前工作目录是 e:\TrailSnap\TrailSnap
            dev_path = os.path.abspath(r"package\server\yolo_ocr\best.pt")
            if os.path.exists(dev_path):
                model_path = dev_path
            else:
                # 尝试另一种相对路径
                dev_path_2 = os.path.abspath(r"..\server\yolo_ocr\best.pt")
                if os.path.exists(dev_path_2):
                     model_path = dev_path_2

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model not found. Checked {model_path}")

        logging.info(f"Loading YOLO model from {model_path}")
        model = YOLO(model_path)
        return model
    except Exception as e:
        logging.error(f"Failed to load YOLO model: {e}")
        raise e

def release_yolo_model(model):
    del model
    logging.info("YOLO model released")

# 注册 YOLO 模型
model_manager.register_model("tickets_yolo", load_yolo_model, release_yolo_model)

class TicketService:
    def detect(self, image_bytes: bytes):
        """
        执行车票检测与识别
        """
        # 获取模型实例
        yolo = model_manager.get_model("tickets_yolo")
        ocr = model_manager.get_model("ocr")

        # 解码图像
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image data")

        # YOLO 推理
        # save=False, verbose=False 以提高性能
        results = yolo.predict(source=img, save=False, verbose=False)
        
        tickets = []
        
        # 确保输出目录存在 (用于调试或模拟中间文件)
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        for result in results:
            boxes = getattr(result, "boxes", None)
            orig_img = getattr(result, "orig_img", img)
            
            if boxes is None:
                continue
                
            for i, box in enumerate(boxes):
                # 获取坐标
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                
                # 边界保护
                h, w = orig_img.shape[:2]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                # 裁剪车票区域
                crop = orig_img[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                
                # 模拟 yolo_ocr.py 的流程：
                # 1. 保存裁剪图像到临时文件
                temp_filename = f"temp_crop_{uuid.uuid4().hex[:8]}.png"
                temp_path = os.path.join(output_dir, temp_filename)
                cv2.imwrite(temp_path, crop)
                
                try:
                    # 2. 对裁剪区域执行 OCR (传入文件路径)
                    # RapidOCR 支持路径输入
                    out = ocr(temp_path)
                except Exception as e:
                    logging.warning(f"OCR inference failed for {temp_path}: {e}")
                    out = None
                finally:
                    # 清理临时图片文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                if isinstance(out, tuple):
                    ocr_result = out[0]
                else:
                    ocr_result = out
                
                # 构造 JSON 数据结构以模拟 yolo_ocr.py 的中间结果
                json_data = {"rec_texts": [], "rec_polys": []}
                if ocr_result:
                    try:
                        # Check for RapidOCROutput object (has txts, boxes, scores attributes)
                        if hasattr(ocr_result, 'txts') and hasattr(ocr_result, 'boxes'):
                            # Handle RapidOCROutput object
                            txts = ocr_result.txts
                            boxes = ocr_result.boxes
                            for i in range(len(txts)):
                                text = txts[i]
                                # Convert numpy array box to list for JSON serialization
                                poly = boxes[i].tolist() if hasattr(boxes[i], 'tolist') else boxes[i]
                                json_data["rec_texts"].append(str(text))
                                json_data["rec_polys"].append(poly)
                        else:
                            # Handle standard list of tuples/lists
                            for item in ocr_result:
                                if isinstance(item, (list, tuple)) and len(item) >= 2:
                                    poly = item[0]
                                    text = item[1]
                                    json_data["rec_texts"].append(str(text))
                                    json_data["rec_polys"].append(poly)
                    except Exception as e:
                         logging.warning(f"OCR result parse failed: {e}")

                # 3. 保存原始OCR结果到JSON (完全对齐 yolo_ocr.py 流程)
                json_filename = f"temp_crop_{uuid.uuid4().hex[:8]}_ocr.json"
                json_path = os.path.join(output_dir, json_filename)
                try:
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)
                    
                    # 4. 从JSON文件中提取文本 (调用 ticket_parser_adapter 中的 extract_text)
                    texts, polys = extract_text(json_path)
                    
                    # 调试日志：打印 OCR 识别到的文本
                    logging.info(f"Ticket detection {i}: extracted texts from JSON: {texts}")

                    # 5. 解析车票信息
                    info = parse_ticket_info(texts, polys)
                    info['detection_id'] = i
                    tickets.append(info)
                    
                except Exception as e:
                    logging.error(f"Error processing JSON flow for ticket {i}: {e}")
                finally:
                    # 清理临时 JSON 文件
                    if os.path.exists(json_path):
                        os.remove(json_path)
                
        return {"tickets": tickets, "count": len(tickets)}

ticket_service = TicketService()
