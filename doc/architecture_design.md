# 架构设计文档

## 1. 整体架构图

TrailSnap 采用典型的前后端分离架构，由前端展示层、后端服务层和数据存储层组成。

```mermaid
graph TD
    User[用户] --> |HTTP/HTTPS| Frontend[前端应用 (Vue 3)]
    
    subgraph Frontend_Layer [前端展示层]
        Frontend --> |Axios| API_Gateway[API网关 (Nginx/FastAPI)]
        Frontend --> |UI Components| ElementPlus[Element Plus]
        Frontend --> |State Management| Pinia[Pinia Store]
    end
    
    subgraph Backend_Layer [后端服务层]
        API_Gateway --> |路由分发| Routers[API Routers]
        Routers --> Services[业务逻辑服务]
        
        subgraph Core_Services [核心服务]
            Services --> PhotoMgr[照片管理]
            Services --> AlbumMgr[相册管理]
            Services --> TaskMgr[任务管理器 (后台任务)]
            Services --> Indexer[索引服务]
            Services --> OCR[OCR识别 (YOLO/Paddle)]
        end
        
        Services --> ORM[SQLAlchemy ORM]
    end
    
    subgraph Data_Layer [数据存储层]
        ORM --> |SQL| DB[(PostgreSQL)]
        PhotoMgr --> |File IO| FileSystem[文件存储]
    end
```

## 2. 技术选型及版本

### 2.1 前端技术栈
- **核心框架**: Vue 3.5.13 (Composition API)
- **UI 组件库**: Element Plus 2.11.9
- **CSS 框架**: TailwindCSS 3.4.17
- **状态管理**: Pinia 3.0.3
- **路由管理**: Vue Router 4.5.0
- **构建工具**: Vite 6.2.0
- **HTTP 客户端**: Axios 1.12.2
- **图表库**: Echarts 6.0.0
- **图标库**: Lucide Vue Next, Mingcute Icon
- **其他**: Video.js (视频播放), html2canvas (截图)

### 2.2 后端技术栈
- **编程语言**: Python 3.12+
- **Web 框架**: FastAPI 0.122.0
- **ASGI 服务器**: Uvicorn 0.38.0
- **ORM**: SQLAlchemy 2.0.44
- **数据库迁移**: Alembic 1.17.2
- **数据库驱动**: psycopg2 (PostgreSQL)
- **任务调度**: APScheduler 3.11.1
- **AI/CV**:
  - PaddleOCR 3.3.2 (OCR文字识别)
  - Ultralytics 8.3.232 (YOLO对象检测)
  - OpenCV (图像处理)
- **依赖管理**: UV (Project configuration in `pyproject.toml`)

### 2.3 数据库
- **PostgreSQL**: 关系型数据库，存储用户、相册、照片元数据、系统设置等。

## 3. 目录结构与模块说明

### 3.1 根目录
- `package/server`: 后端服务代码
- `package/website`: 前端应用代码
- `doc`: 项目文档

### 3.2 后端结构 (`package/server`)
- **app/**: 核心应用代码
  - `api/`: API 路由定义 (EndPoints)，按功能模块划分 (user, album, photo, etc.)
  - `core/`: 核心配置与工具 (Logger, Config)
  - `crud/`: 数据库 CRUD 操作封装
  - `db/`: 数据库模型 (Models) 与会话管理 (Session)
  - `schemas/`: Pydantic 数据模型 (Request/Response schemas)
  - `service/`: 复杂业务逻辑与后台服务 (TaskManager, Indexer, Storage)
  - `utils/`: 通用工具函数 (Exif解析, 文件名处理)
- **railway/**: 铁路相关功能模块 (独立的数据处理与同步逻辑)
- **yolo_ocr/**: OCR 与票据识别相关模型与脚本

### 3.3 前端结构 (`package/website`)
- **src/**: 源代码
  - `api/`: 后端接口封装
  - `assets/`: 静态资源 (图片, CSS)
  - `components/`: 通用 Vue 组件 (PhotoGallery, TrainTicket, etc.)
  - `composables/`: 组合式函数 (Hooks)
  - `layouts/`: 页面布局组件
  - `router/`: 路由配置
  - `stores/`: Pinia 状态管理仓库
  - `types/`: TypeScript 类型定义
  - `views/`: 页面视图 (Pages)
