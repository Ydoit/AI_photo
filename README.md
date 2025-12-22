# TrailSnap 足迹相册

TrailSnap 是一个智能化的 AI 相册应用，致力于帮助用户轻松记录、整理和回顾自己的出行经历。通过现代化的 UI 设计和强大的后端 AI 处理能力，让每一张照片和每一段旅程都成为值得珍藏的记忆。

## ✨ 核心特色

- **📷 智能相册**: 支持瀑布流布局，按比例完美展示照片。
- **🤖 AI 赋能**: 集成 OCR 文字识别（车票识别）和对象检测（YOLO），支持智能分类与检索。
- **🚆 行程记录**: 特有的火车票/行程管理功能，自动识别车票信息并生成时间轴。
- **🎨 现代化 UI**: 基于 Vue 3 + Element Plus + TailwindCSS 构建，支持深色/浅色主题切换，全端响应式适配。
- **⚡ 高性能**: 前端虚拟滚动，后端异步处理，支持分批加载与高性能图片服务。

## 🛠️ 技术栈

### 前端 (Web)
- **框架**: Vue 3, TypeScript, Vite
- **UI**: Element Plus, TailwindCSS
- **状态管理**: Pinia
- **路由**: Vue Router
- **可视化**: ECharts

### 后端 (Server)
- **核心**: Python 3.12+, FastAPI
- **数据库**: PostgreSQL, SQLAlchemy (Async)
- **AI/CV**: PaddleOCR（AI 微服务）, InsightFace（AI 微服务）, YOLO (Ultralytics 脚本), OpenCV
- **任务调度**: Custom Task Manager

## 📂 目录结构

```
TrailSnap/
├── package/
│   ├── server/      # 后端 FastAPI 服务
│   └── website/     # 前端 Vue 应用
│   └── ai/          # AI 微服务 (OCR/Face)
├── doc/             # 项目技术文档
└── ...
```

## 🚀 快速开始

### 后端启动

1. 进入后端目录:
   ```bash
   cd package/server
   ```
2. 安装依赖 (推荐使用 uv):
   ```bash
   pip install -r requirements.txt
   # 或者
   uv sync
   ```
3. 配置环境变量 (参考 `.env.example`，需配置数据库连接)。
4. 启动服务:
   ```bash
   python main.py
   # 或使用 uvicorn
   uvicorn app.main:app --reload
   ```

### AI 微服务启动（OCR/人脸）

1. 进入 AI 目录:
   ```bash
   cd package/ai
   ```
2. 安装依赖（建议使用 GPU 版本 PaddlePaddle，如无 GPU 可改为 CPU 版本）:
   ```bash
   pip install -r requirements.txt
   ```
3. 启动 AI 服务:
   ```bash
   python main.py
   # 或
   uvicorn app.main:app --reload --port 8001
   ```
4. 后端服务默认通过 `config_manager` 使用 `http://localhost:8001` 调用 AI 服务。

### 前端启动

1. 进入前端目录:
   ```bash
   cd package/website
   ```
2. 安装依赖:
   ```bash
   pnpm install
   ```
3. 启动开发服务器:
   ```bash
   pnpm dev
   ```

## 📦 部署要求

- **数据库**: PostgreSQL 可用连接，建议创建专用库与用户，设置 `data/.env` 中的数据库连接串。
- **AI 微服务**: 默认端口 `8001`，需与后端互通；如使用 GPU，请安装对应 CUDA 版本的 PaddlePaddle-GPU。
- **存储**: 后端需具备读写图片文件的权限；为提升浏览性能，建议开启缩略图生成。
- **环境变量**:
  - 后端：`data/.env`（示例），包含数据库连接、存储路径等。
  - AI：`INSIGHTFACE_MODEL_PATH`（人脸模型缓存路径，可选）、端口/跨域配置等。

## 🧭 功能概览

- 智能相册：瀑布流展示、相册管理、照片元数据解析。
- AI 能力：OCR 识别（支持文本检测与识别、多边形坐标返回），人脸检测与特征抽取。
- 行程票据：火车票信息管理，支持创建、编辑、删除与列表展示。
- 数据可视化：出行统计图表、时间轴与线路里程。
- 高性能：异步任务处理、虚拟滚动、坐标归一化绘制。

## 📚 文档

更多详细技术文档请参阅 `doc/` 目录：
- [架构设计文档](doc/architecture_design.md)
- [前端框架分析](doc/frontend_analysis.md)
- [后端框架分析](doc/backend_analysis.md)

## 🔍 备注

- YOLO_OCR 脚本位于 `package/server/yolo_ocr/`，用于票据区域检测与字段解析的实验/批处理场景；
  AI 微服务当前提供通用 OCR 接口（`/ocr/predict`），服务端任务将结果落库并在前端展示。
