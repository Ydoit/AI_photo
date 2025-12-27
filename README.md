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

### docker一键启动

1. 确保已安装 Docker 和 Docker Compose。

2. docker-compose 和 初始化脚本

docker-compose.yml 配置文件
```yml
services:
  postgres:
    image: pgvector/pgvector:pg18-trixie
    container_name: postgres_container
    restart: always
    environment:
      POSTGRES_DB: trailsnap
      POSTGRES_USER: trailsnap
      POSTGRES_PASSWORD: trailsnap
      # 可选：设置PostgreSQL配置（优化向量搜索性能）
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C --lc-ctype=C"
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5532:5432"                  # 端口映射
    volumes:
      - ./pg_data:/var/lib/postgresql/data  # 数据持久化
      # 挂载初始化脚本目录，自动创建pgvector扩展
      - ./init-scripts:/docker-entrypoint-initdb.d/
    # 新增：健康检查（确保数据库就绪后，应用再连接）
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trailsnap -d trailsnap -p 5432"]
      interval: 5s    # 每5秒检查一次
      timeout: 5s     # 超时时间5秒
      retries: 5      # 最多重试5次
      start_period: 10s  # 容器启动后10秒再开始检查

  server:
    image: siyuan044/trailsnap-server:master
    restart: always
    expose: [ "8000" ]
    ports: [ "8800:8000" ]
    networks: [ app-network ]
    volumes:
      - ./data:/app/data        # 挂载数据目录
      - F:\Photos:/app/Photos/  # 挂载本地照片目录
    environment:
      - DB_URL=postgresql://trailsnap:trailsnap@postgres:5432/trailsnap
      - RAILWAY_DB_URL=postgresql://trailsnap:trailsnap@postgres:5432/railway
      - AI_API_URL=http://ai:8001
    depends_on:
      - postgres  # 确保数据库服务启动后再启动应用

  ai:
    image: siyuan044/trailsnap-ai:master
    restart: always
    expose: [ "8001" ]
    ports: [ "8801:8001" ]
    networks: [ app-network ]
    volumes:
      - ./data:/app/data        # 挂载数据目录

  frontend:
    image: siyuan044/trailsnap-frontend:master
    restart: always
    ports: [ "8082:80" ]
    depends_on: [ server ]
    networks: [ app-network ]

networks:
  app-network:
    driver: bridge
```

在项目根目录下，创建一个名为 `init-scripts` 的文件夹，用于存放初始化脚本。
**初始化脚本**: 需要在 `docker-compose.yml` 中指定的 `init-scripts` 目录下创建 `01_create_vector_extension.sql` (如果尚未创建)。

```sql
-- 01_create_vector_extension.sql
-- 连接目标数据库（必须指定，否则默认连postgres库）
\c trailsnap;
-- 创建pgvector扩展（IF NOT EXISTS避免重复创建）
CREATE EXTENSION IF NOT EXISTS vector;

\c postgres
SELECT 'CREATE DATABASE railway'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'railway')\gexec
```

1. 启动服务

```bash
docker-compose up -d
```

### 源码部署

[源码部署](doc/developer_guide.md)

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
