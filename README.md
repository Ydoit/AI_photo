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
- **可视化**: Echarts

### 后端 (Server)
- **核心**: Python 3.12+, FastAPI
- **数据库**: PostgreSQL, SQLAlchemy (Async)
- **AI/CV**: PaddleOCR, YOLO (Ultralytics), OpenCV
- **任务调度**: Custom Task Manager

## 📂 目录结构

```
TrailSnap/
├── package/
│   ├── server/      # 后端 FastAPI 服务
│   └── website/     # 前端 Vue 应用
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

## 📚 文档

更多详细技术文档请参阅 `doc/` 目录：
- [架构设计文档](doc/architecture_design.md)
- [前端框架分析](doc/frontend_analysis.md)
- [后端框架分析](doc/backend_analysis.md)
