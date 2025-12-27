# TrailSnap Backend Service

TrailSnap 的后端核心服务，基于 FastAPI 构建，负责业务逻辑处理、数据存储与检索、以及与 AI 服务的交互。

## 目录
1. [前置条件](#前置条件)
2. [快速开始](#快速开始)
3. [数据库配置](#数据库配置)
4. [配置说明](#配置说明)
5. [开发指南](#开发指南)

## 前置条件

在启动 Server 之前，必须先启动 PostgreSQL 数据库，并确保安装了 `pgvector` 插件。

### 数据库启动 (Docker Compose)

推荐使用 Docker Compose 启动数据库，已配置好 `pgvector` 环境。

1. **配置文件**: 参考[`docker-compose-pg.yml`](../../docker-compose/docker-compose-pg.yml)。
2. **初始化脚本**: 需要在 `docker-compose-pg.yml` 中指定的 `init-scripts` 目录下创建 `01_create_vector_extension.sql` (如果尚未创建)。

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

3. **启动命令**:
   ```bash
   docker-compose -f docker-compose-pg.yml up -d
   ```

## 快速开始

### 1. 安装依赖

Python 版本要求: >=3.10 (开发环境使用 3.12)

推荐使用 `uv` 包管理器：
```bash
pip install uv
uv sync
```

或者使用 `pip`:
```bash
pip install -r requirements.txt
```

### 2. 环境变量配置

在 `package/server/data` 目录下创建 `.env` 文件，写入以下配置：

```env
# 主数据库 (根据实际情况修改 host, user, password)
DB_URL=postgresql://msi:msi4090@localhost:5532/trailsnap

# 铁路数据库
RAILWAY_DB_URL=postgresql://msi:msi4090@localhost:5532/railway

# AI 服务地址
AI_SERVICE_URL=http://localhost:8001
```

### 3. 运行服务

```bash
# 开发模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问 Swagger 文档: http://localhost:8000/docs

## 数据库迁移

本项目使用 **Alembic** 进行数据库版本控制。

- **初始化/生成迁移脚本**:
  ```bash
  alembic revision --autogenerate -m "描述"
  ```
- **执行迁移**:
  ```bash
  alembic upgrade head
  ```

## 目录结构

- `app/`: 应用代码
  - `api/`: 路由接口
  - `core/`: 核心配置
  - `crud/`: 数据库操作
  - `db/`: 数据库模型
  - `schemas/`: Pydantic 验证模型
  - `service/`: 业务服务
- `railway/`: 铁路数据相关逻辑
- `data/`: 配置文件与数据存储
