# TrailSnap 行影集

TrailSnap 是一个智能化的 AI 相册应用，致力于帮助用户轻松记录、整理和回顾自己的出行经历。通过现代化的 UI 设计和强大的后端 AI 处理能力，让每一张照片和每一段旅程都成为值得珍藏的记忆。

## ✨ 核心特色

- **📷 智能相册**: 人物识别、智能分类、OCR识别。
- **🚆 行程记录**: 特有的火车票、行程、景区/演唱会门票管理功能，自动识别票据信息。
- **🤖 AI 赋能**: 一句话让AI帮你生成旅行日记。
  - AI自动剪视频生成VLOG
  - AI修图，自动识别高质量照片

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

[查看后端文档](./package/server/README.md)

### AI 微服务启动（OCR/人脸）

[查看 AI 微服务文档](./package/ai/README.md)

### 前端启动

[查看前端文档](./package/website/README.md)

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
- [开发者文档](doc/developer_guide.md)
- [用户指南](doc/user_guide.md)

## 🔍 备注

- YOLO_OCR 脚本位于 `package/server/yolo_ocr/`，用于票据区域检测与字段解析的实验/批处理场景；
  AI 微服务当前提供通用 OCR 接口（`/ocr/predict`），服务端任务将结果落库并在前端展示。
