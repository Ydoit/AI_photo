---
title: Docker 部署（通用）
---

# Docker 部署（通用）

本章面向 NAS/家庭服务器场景：用 Docker Compose 一次性启动 TrailSnap 的前端、后端、数据库与 AI 服务，并把你的照片目录挂载进来。

如果你还没看过安装指南，建议先读：[/docs/guide/install](/docs/guide/install)

## 1. 目录规划（建议）

在 NAS 上先准备一个共享文件夹作为 TrailSnap 的“项目目录”，建议包含两类数据：

- **应用数据**：数据库与应用运行数据（需要长期持久化）
- **照片目录**：你自己的照片库（建议只读挂载）

示例结构（仅示意）：

```
trailsnap/
  docker-compose.yml
  data/
  pg_data/
```

## 2. Docker Compose（推荐模板）

下面的 compose 与安装指南保持一致，你只需要修改两处：

- `server.volumes` 里照片目录的宿主机路径
- 如有端口冲突，修改 `ports` 映射

```yaml
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
    image: siyuan044/trailsnap-server:latest
    restart: always
    expose: [ "8000" ]
    ports: [ "8800:8000" ]
    networks: [ app-network ]
    volumes:
      - ./data:/app/data
      - /path/to/your/photos:/app/Photos/
    environment:
      - DB_URL=postgresql://trailsnap:trailsnap@postgres:5432/trailsnap
      - RAILWAY_DB_URL=postgresql://trailsnap:trailsnap@postgres:5432/railway
      - AI_API_URL=http://ai:8001
    depends_on:
      postgres:
        condition: service_healthy
        restart: true

  ai:
    image: siyuan044/trailsnap-ai:latest
    restart: always
    expose: [ "8001" ]
    ports: [ "8801:8001" ]
    networks: [ app-network ]
    volumes:
      - ./data:/app/data

  frontend:
    image: siyuan044/trailsnap-frontend:latest
    restart: always
    ports: [ "8082:80" ]
    depends_on: [ server ]
    networks: [ app-network ]

networks:
  app-network:
    driver: bridge
```

## 3. 启动与验证

在 `docker-compose.yml` 所在目录执行：

```bash
docker-compose up -d
```

启动后常用入口：

- 前端：`http://<NAS_IP>:8082`
- 后端 API：`http://<NAS_IP>:8800/docs`
- AI 服务：`http://<NAS_IP>:8801/docs`

## 4. NAS 场景常见问题

### 4.1 路径怎么写才正确？

在 NAS 上请以“共享文件夹的真实路径”为准。不同系统的路径显示方式不同，但原则只有一个：确保容器内的 `/app/Photos/` 能看到你的照片文件。

### 4.2 权限不足导致扫描不到照片

如果照片目录是只读共享或权限隔离，容器可能无法读取。建议：

- 给容器运行账号授予该共享文件夹的读取权限
- 或把照片目录挂载为只读并确保宿主机侧权限允许读取

### 4.3 端口冲突

NAS 上常见 80/443/8080 等端口容易被占用。TrailSnap 默认使用 8082/8800/8801/5532，如冲突可自行改映射，例如：

```yaml
ports: [ "18082:80" ]
```

## 5. NAS 具体教程

- [绿联 NAS 部署](/docs/guide/docker/ugreen)
- [极空间部署](/docs/guide/docker/zspace)
- [飞牛OS 部署](/docs/guide/docker/fnos)

