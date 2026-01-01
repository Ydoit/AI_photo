# TrailSnap 行影集

TrailSnap 是一个智能化的 AI 相册应用，致力于帮助用户轻松记录、整理和回顾自己的出行经历。通过强大的 AI 处理能力，让每一张照片和每一段旅程都成为值得珍藏的记忆。

我相信未来每个人（至少每个家庭）都有一个属于自己的 AI 数据中心，而相册是数据中心的一个重要数据来源，它留存了你生活中的很多瞬间，而 AI 相册则是将这些瞬间转化为有价值的记忆，它可以帮你默默地记录下相册里的车票、景点门票，可以帮你记录旅行中的所见所闻，可以帮你自动整理出可以发朋友圈的照片（甚至帮你准备好文案），可以帮你剪一段15s的短视频······。

所以，我给这个项目命名为 **《行影集》**，在这里你的数据才 “真正属于你”。

## ✨ 核心特色

- **📷 智能相册**: 人物识别、智能分类、OCR识别。
- **🚆 行程记录**: 特有的火车票、行程、景区/演唱会门票管理功能，自动识别票据信息。（正在开发中）
- **🤖 AI 赋能**: 一句话让AI帮你生成旅行日记。（待开发）
  - AI自动剪视频生成VLOG
  - AI修图，自动识别高质量照片

## 🧭 功能概览

- 智能相册：瀑布流展示、相册管理、位置解析。
- AI 能力：OCR 识别，人脸检测与特征抽取，智能分类。
- 行程票据：火车票信息管理，支持创建、编辑、删除与列表展示。
- 数据可视化：出行统计图表、时间轴与线路里程。
- 年度报告：自动生成2025年的出行统计报告，包括照片墙、出行城市、出行景点、行程时间轴、线路里程等。

## 2025 年度报告（预览版）

2025 相册年度报告正在制作中，敬请期待！（docker部署可以体验半成品，也可以先star项目等待后续发布正式版）

![年度报告](./doc/image/年度报告.jpg)

## 🚀 快速开始

### docker一键启动

1. 确保已安装 Docker 和 Docker Compose。

2. docker-compose

docker-compose.yml 配置文件（注意修改挂载路径为本地路径，不然无法扫描本地照片目录）
```yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg18-trixie
    container_name: postgres_container
    restart: always
    environment:
      POSTGRES_DB: trailsnap
      POSTGRES_USER: trailsnap
      POSTGRES_PASSWORD: trailsnap
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C --lc-ctype=C"
      PGDATA: /var/lib/postgresql/data/pgdata
    networks: [ app-network ]
    ports:
      - "5532:5432"
    volumes:
      - ./pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trailsnap -d trailsnap -p 5432"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

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
      postgres:
        condition: service_healthy
        restart: true

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

1. 启动服务

```bash
docker-compose up -d
```

### 源码部署

[源码部署](doc/developer_guide.md)

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

## 📚 文档

更多详细技术文档请参阅 `doc/` 目录：
- [架构设计文档](doc/architecture_design.md)
- [前端框架分析](doc/frontend_analysis.md)
- [后端框架分析](doc/backend_analysis.md)
- [开发者文档](doc/developer_guide.md)
- [用户指南](doc/user_guide.md)

## 🔍 备注

