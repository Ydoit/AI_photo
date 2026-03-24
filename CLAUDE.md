# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TrailSnap（行影集）是一个智能 AI 相册应用，采用前后端分离架构，包含三个主要服务：
- **前端** (`package/website`): Vue 3 + TypeScript + Vite + Element Plus + TailwindCSS
- **后端** (`package/server`): Python FastAPI + SQLAlchemy + Alembic
- **AI服务** (`package/ai`): 独立微服务，提供 OCR、人脸识别、目标检测能力

数据库使用 PostgreSQL + pgvector（向量搜索）。

## 常用命令

### 后端服务 (package/server)
```bash
cd package/server

# 安装依赖
uv sync

# 启动服务（推荐，自动执行数据库初始化和迁移）
python start.py

# 开发模式热重载
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 数据库迁移
alembic revision --autogenerate -m "描述修改内容"
alembic upgrade head
```

### 前端应用 (package/website)
```bash
cd package/website

# 安装依赖
pnpm install

# 开发服务器
pnpm dev

# 构建
pnpm build
```

### AI 服务 (package/ai)
```bash
cd package/ai

# 安装依赖 (CPU版本)
uv sync --extra cpu

# GPU版本
uv sync --extra gpu

# 启动服务
uvicorn main:app --reload --port 8001
```

## 架构要点

### 服务端口
- 前端开发服务器: `5176`
- 后端 API: `8000`
- AI 微服务: `8001`
- PostgreSQL: `5432` (Docker 映射 `5532`)

### 后端目录结构 (`package/server/app`)
- `api/`: API 路由，按功能模块划分（photo, album, face, ocr, agent 等）
- `core/`: 配置管理、日志、安全
- `crud/`: 数据库 CRUD 操作封装
- `db/models/`: SQLAlchemy 数据模型
- `schemas/`: Pydantic 请求/响应模型
- `service/`: 业务逻辑层（索引器、人脸聚类、Agent 等）

### 前端目录结构 (`package/website/src`)
- `api/`: 后端接口封装
- `components/`: 通用组件（PhotoGallery、PhotoLightbox 等）
- `composables/`: 组合式函数（hooks）
- `stores/`: Pinia 状态管理
- `views/`: 页面视图
- `router/`: 路由配置

### 关键业务流程
1. **照片索引**: `service/indexer.py` 负责扫描、解析 EXIF、调用 AI 服务
2. **人脸识别**: 后端调用 AI 服务 → `service/face_cluster.py` 聚类
3. **智能相册**: `api/agent.py` + `service/agent/` 实现 AI 对话式相册查询
4. **票据识别**: YOLO + OCR 识别火车票/机票，存储于独立数据表

### 数据库注意事项
- 修改 `db/models/` 后必须执行 Alembic 迁移
- pgvector 扩展用于照片向量相似度搜索
- Railway 模块使用独立数据库连接

## 环境配置

后端 `.env` 文件位置: `package/server/data/.env`
```env
DB_URL=postgresql://user:password@localhost:5532/trailsnap
RAILWAY_DB_URL=postgresql://user:password@localhost:5532/railway
AI_API_URL=http://localhost:8001
```
