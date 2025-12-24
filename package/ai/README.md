# TrailSnap AI Service

TrailSnap 的 AI 微服务模块，负责处理所有计算机视觉相关的任务，包括 OCR（文字识别）、人脸检测与识别、物体检测等。

## 功能特性

- **OCR 识别**: 基于 PaddleOCR，支持多语言文字识别，专门针对火车票、行程单优化。
- **人脸识别**: 基于 InsightFace，支持人脸检测、特征提取、人脸聚类。
- **物体检测**: 基于 YOLO，用于识别照片场景和物体。

## 环境要求

- Python 3.10+
- CUDA (如果使用 GPU 加速)

## 安装

1. 进入目录：
   ```bash
   cd package/ai
   ```

2. 安装依赖：
   
   **CPU 版本**:
   ```bash
   pip install -r requirements.txt
   ```

   **GPU 版本** (推荐，需先安装 CUDA):
   ```bash
   pip install -r requirements-gpu.txt
   ```
   *(注意：如果 `requirements-gpu.txt` 不存在，请手动安装 `paddlepaddle-gpu` 和 `onnxruntime-gpu`)*

## 运行

使用 Uvicorn 启动服务：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

服务默认运行在 `8001` 端口。

## API 文档

启动服务后，访问 Swagger UI 查看接口文档：
http://localhost:8001/docs
