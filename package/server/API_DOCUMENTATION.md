# TrailSnap Server API 文档

本文档详细描述了 TrailSnap 后端服务的所有 API 接口，遵循 OpenAPI 3.0 规范风格。

## 目录

- [概述](#概述)
- [认证机制](#认证机制)
- [API 模块](#api-模块)
  - [认证模块 (Auth)](#认证模块-auth)
  - [用户模块 (User)](#用户模块-user)
  - [照片模块 (Photo)](#照片模块-photo)
  - [相册模块 (Album)](#相册模块-album)
  - [人脸识别模块 (Face)](#人脸识别模块-face)
  - [OCR 模块](#ocr-模块)
  - [搜索模块 (Search)](#搜索模块-search)
  - [位置模块 (Location)](#位置模块-location)
  - [智能助手模块 (Agent)](#智能助手模块-agent)
  - [媒体模块 (Media)](#媒体模块-media)
  - [任务模块 (Tasks)](#任务模块-tasks)
  - [设置模块 (Settings)](#设置模块-settings)
  - [统计模块 (Stats)](#统计模块-stats)
  - [智能分类模块 (Classification)](#智能分类模块-classification)
  - [火车票模块 (Train Ticket)](#火车票模块-train-ticket)
  - [索引模块 (Index)](#索引模块-index)

---

## 概述

- **基础路径**: `/api`
- **服务端口**: `8000`
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

#### 成功响应
```json
{
  "id": "uuid",
  "field": "value",
  ...
}
```

#### 错误响应
```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 资源创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token 无效或过期） |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 413 | 请求实体过大 |
| 500 | 服务器内部错误 |
| 502 | 上游服务错误（如 AI 服务） |

---

## 认证机制

TrailSnap 使用 OAuth2 Bearer Token 认证方式。

### Token 类型

1. **JWT Token**: 用户登录后获取的标准访问令牌
2. **Agent Token**: 第三方应用访问令牌，以 `ts_` 开头

### 认证头格式

```
Authorization: Bearer <token>
```

### Token 过期处理

- Token 过期时返回 `401 Unauthorized`，响应体包含 `"Token has expired"`
- 前端应捕获此错误并引导用户重新登录

---

## API 模块

### 认证模块 (Auth)

**路由前缀**: `/auth`

#### POST /auth/login

用户登录，获取访问令牌。

**请求体**: `application/x-www-form-urlencoded`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

**响应**: `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应**:
- `401`: 用户名或密码错误
- `403`: 密码错误次数过多，用户已被锁定

---

#### POST /auth/register

注册新用户。

**请求体**: `application/json`

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "security_question": "string?",
  "security_answer": "string?"
}
```

**响应**: `200 OK` - 返回用户信息

**说明**: 第一个注册的用户自动成为超级管理员。

---

#### POST /auth/check-reset-user

检查密码重置用户是否存在。

**请求体**: `application/json`

```json
{
  "username_or_email": "string"
}
```

**响应**: `200 OK`

```json
{
  "security_question": "您的小学名称是？"
}
```

---

#### POST /auth/reset-password

通过密保问题重置密码。

**请求体**: `application/json`

```json
{
  "username_or_email": "string",
  "security_answer": "string",
  "new_password": "string"
}
```

---

#### GET /auth/status

获取系统认证状态（无需认证）。

**响应**:

```json
{
  "has_users": true
}
```

---

### 用户模块 (User)

**路由前缀**: `/users`

#### GET /users/

获取用户列表。普通用户仅返回自己，超级管理员返回所有用户。

**响应**: 用户对象数组

---

#### POST /users/

创建新用户（仅超级管理员）。

---

#### GET /users/me

获取当前登录用户信息。

**响应**: 用户对象

---

#### PUT /users/{user_id}/password

更新用户密码。

**请求体**:

```json
{
  "password": "new_password"
}
```

---

#### DELETE /users/{user_id}

删除用户。

---

### 照片模块 (Photo)

**路由前缀**: `/photos`

#### GET /photos

获取照片列表，支持多条件筛选。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| skip | int | 分页偏移量，默认 0 |
| limit | int | 每页数量，默认 100 |
| album_id | UUID | 按相册筛选 |
| face_id | UUID | 按人物筛选 |
| tag_id | UUID | 按标签筛选 |
| start_time | datetime | 开始时间 |
| end_time | datetime | 结束时间 |
| years | List[int] | 年份列表 |
| city | string | 城市 |
| cities | List[string] | 城市列表 |
| province | string | 省份 |
| country | string | 国家 |
| make | string | 相机品牌 |
| model | string | 相机型号 |
| image_type | string | 图片类型（photo/video） |
| file_type | string | 文件格式（jpg/png/heic 等） |
| tag | string | 标签名称 |
| lat_min, lat_max, lng_min, lng_max | float | 经纬度范围 |
| radius, center_lat, center_lng | float | 圆形范围筛选 |
| ids | List[UUID] | 指定照片 ID 列表 |

---

#### POST /photos/batch/create

批量创建照片记录。

**请求体**:

```json
{
  "items": [
    {
      "photo": { "filename": "string", ... },
      "file_path": "string",
      "photo_id": "UUID?"
    }
  ]
}
```

---

#### POST /photos/batch

批量操作照片。

**请求体**:

```json
{
  "photo_ids": ["UUID"],
  "action": "add_to_album | remove_from_album | delete",
  "album_id": "UUID?"
}
```

---

#### DELETE /photos/batch

批量删除照片。

**请求体**:

```json
{
  "photo_ids": ["UUID"]
}
```

---

#### GET /photos/{photo_id}

获取单张照片详情。

---

#### PUT /photos/{photo_id}

更新照片信息。

---

#### DELETE /photos/{photo_id}

删除单张照片（同时删除文件）。

---

#### GET /photos/{photo_id}/metadata

获取照片元数据。

**响应**: 包含 EXIF 信息、关联相册、人物、标签等

---

#### PUT /photos/{photo_id}/metadata

更新照片元数据。

---

#### GET /photos/{photo_id}/tags

获取照片标签列表。

---

#### POST /photos/{photo_id}/tags

为照片添加标签。

**请求体**:

```json
{
  "tag_name": "string",
  "confidence": 1.0
}
```

---

#### DELETE /photos/{photo_id}/tags/{tag_id}

删除照片标签。

---

#### GET /photos/{photo_id}/description

获取照片 AI 描述和评分。

---

#### GET /photos/on-this-day

获取"那年今日"的照片。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| month | int | 月份，默认当前月 |
| day | int | 日期，默认当前日 |
| year | int | 参考年份，默认当前年 |
| limit | int | 返回数量，默认 10 |

---

#### 相似照片任务接口

##### POST /photos/similar/tasks

创建相似照片聚类任务。

**查询参数**: `threshold` - 相似度阈值，默认 0.9

##### GET /photos/similar/tasks/latest

获取最新的相似照片任务。

##### GET /photos/similar/tasks/{task_id}

获取指定任务状态。

##### GET /photos/similar/tasks/{task_id}/result

获取任务结果（相似照片组列表）。

##### DELETE /photos/similar/tasks/{task_id}

取消/删除任务。

---

#### GET /photos/cleanup

获取待清理照片列表（按评分排序）。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| skip | int | 偏移量 |
| limit | int | 数量 |
| sort_by | string | 排序方式：asc（低分优先）/ desc（高分优先）|

---

### 相册模块 (Album)

**路由前缀**: `/albums`

#### POST /albums

创建相册。

**请求体**:

```json
{
  "name": "string",
  "description": "string?",
  "type": "normal | conditional | smart",
  "conditions": {}?
}
```

**说明**:
- `normal`: 普通相册，手动添加照片
- `conditional`: 条件相册，根据条件自动筛选
- `smart`: 智能相册，根据描述通过 AI 向量搜索匹配

---

#### GET /albums

获取相册列表。

---

#### GET /albums/{album_id}

获取相册详情。

---

#### PUT /albums/{album_id}

更新相册信息。

---

#### DELETE /albums/{album_id}

删除相册（不删除照片）。

---

#### PUT /albums/{album_id}/cover

设置相册封面。

**请求体**:

```json
{
  "photo_id": "UUID"
}
```

---

#### POST /albums/{album_id}/photos

上传照片到相册。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | 照片文件 |

---

#### GET /albums/{album_id}/photos

获取相册内的照片列表。

---

#### DELETE /albums/{album_id}/photos/{photo_id}

从相册中移除照片（不删除照片本身）。

---

### 人脸识别模块 (Face)

**路由前缀**: `/faces`

#### POST /faces/identities

创建新人物。

**请求体**:

```json
{
  "identity_name": "string",
  "description": "string?"
}
```

---

#### GET /faces/identities

获取人物列表。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| limit | int | 每页数量，默认 20 |
| types | List[string] | 类型筛选：named, unnamed, hidden |

---

#### PUT /faces/identities/{id}

更新人物信息。

---

#### DELETE /faces/identities/{id}

删除人物（软删除，解除人脸关联）。

---

#### POST /faces/identities/{id}/add-photos

添加照片到人物。

**请求体**:

```json
{
  "photo_ids": ["UUID"]
}
```

**说明**: 如果照片中无人脸，会自动触发 AI 识别。

---

#### POST /faces/identities/{id}/remove-photos

从人物中移除照片。

**请求体**:

```json
{
  "photo_ids": ["UUID"]
}
```

---

#### GET /faces/identities/{id}/photos

获取人物的照片列表。

---

#### PUT /faces/identities/{id}/cover

设置人物封面。

**请求体**:

```json
{
  "photo_id": "UUID"
}
```

---

#### POST /faces/identities/merge

合并多个人物。

**请求体**:

```json
{
  "target_id": "UUID",
  "source_ids": ["UUID"]
}
```

---

#### POST /faces/identities/{id}/rescan

重新扫描人物人脸。

---

### OCR 模块

**路由前缀**: `/ocr`

#### GET /ocr

获取照片的 OCR 识别结果。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| photo_id | UUID | 照片 ID（必填）|

**响应**:

```json
{
  "count": 5,
  "records": [
    {
      "text": "识别的文字",
      "confidence": 0.95,
      "polygon": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    }
  ]
}
```

---

#### DELETE /ocr/{photo_id}

删除照片的 OCR 记录。

---

### 搜索模块 (Search)

**路由前缀**: `/search`

#### GET /search/suggestions

获取搜索建议。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词（至少 1 字符）|

**响应**: 建议列表，类型包括 person, location, ocr, album, filename, folder, tag, scene

---

#### POST /search/text

文本搜索照片。

**请求体**:

```json
{
  "text": "搜索内容",
  "limit": 20,
  "skip": 0,
  "threshold": 0.2,
  "type": "ocr | location | person | album | folder | filename | tag | scene"
}
```

**说明**:
- 指定 `type` 时使用元数据精确匹配
- 不指定 `type` 时使用 AI 向量语义搜索

---

#### POST /search/image

以图搜图。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | 图片文件 |
| limit | int | 返回数量 |
| threshold | float | 相似度阈值 |

---

### 位置模块 (Location)

**路由前缀**: `/locations`

#### GET /locations/search

搜索位置。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| q | string | 搜索关键词 |

---

#### GET /locations/years

获取所有照片的拍摄年份。

---

#### GET /locations

获取位置列表。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| level | string | 分组级别：city, province, district, scene |
| year | int | 年份筛选 |
| skip | int | 偏移量 |
| limit | int | 数量 |

---

#### GET /locations/distribution

获取位置分布数据（用于地图展示）。

---

#### GET /locations/statistics

获取位置统计数据。

**响应**:

```json
{
  "total_provinces": 10,
  "total_cities": 50,
  "total_districts": 100
}
```

---

#### GET /locations/markers

获取地图标记点。

---

#### GET /locations/{name}/photos

获取指定位置的照片。

---

#### 景区接口

##### POST /locations/scenes

创建自定义景区。

**请求体**:

```json
{
  "name": "景区名称",
  "polygon": [[lng, lat], ...]
}
```

##### GET /locations/scenes/list

获取所有景区列表。

##### GET /locations/scenes/{scene_id}

获取景区详情。

##### PUT /locations/scenes/{scene_id}

更新景区信息。

##### DELETE /locations/scenes/{scene_id}

删除景区（系统默认景区不可删除）。

---

### 智能助手模块 (Agent)

**路由前缀**: `/agent`

#### POST /agent/chat

与智能相册助手对话。

**请求体**:

```json
{
  "message": "帮我找去年在海边的照片",
  "session_id": "UUID?",
  "stream": false
}
```

**响应**:

```json
{
  "response": "我找到了 15 张去年在海边的照片...",
  "session_id": "UUID"
}
```

**流式响应**: 设置 `stream: true` 时返回 `text/event-stream`

---

#### GET /agent/sessions

获取会话列表。

---

#### POST /agent/sessions

创建新会话。

---

#### DELETE /agent/sessions/{session_id}

删除会话。

---

#### PUT /agent/sessions/{session_id}/pin

置顶/取消置顶会话。

**查询参数**: `is_pinned` - boolean

---

#### GET /agent/sessions/{session_id}/messages

获取会话消息历史。

---

#### DELETE /agent/messages

删除会话消息。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |
| message_ids | string | 消息 ID 列表（逗号分隔），为空则删除全部 |

---

### 媒体模块 (Media)

**路由前缀**: `/media`

#### POST /media

上传照片/视频。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | 媒体文件 |
| album_id | UUID | 相册 ID（可选）|

**说明**: 上传后自动创建元数据提取、人脸识别、OCR 等任务。

---

#### GET /media/{photo_id}/file

获取原始媒体文件。支持 Range 请求（视频流式播放）。

---

#### GET /media/{photo_id}/thumbnail

获取缩略图。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| size | string | 尺寸：small（默认）/ medium |

---

#### GET /media/{photo_id}/video

获取 Live Photo 的视频部分。

---

#### 分片上传接口

##### POST /media/upload/init

初始化分片上传。

**响应**:

```json
{
  "upload_id": "UUID"
}
```

##### POST /media/upload/chunk

上传分片。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| upload_id | UUID | 上传会话 ID |
| chunk_index | int | 分片序号 |
| file | File | 分片数据 |

##### POST /media/upload/finish

完成分片上传。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| upload_id | UUID | 上传会话 ID |
| file_name | string | 文件名 |
| album_id | UUID | 相册 ID（可选）|

---

#### GET /media/geojson

获取行政区划 GeoJSON 数据。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| level | string | 级别：province, city, district |

---

### 任务模块 (Tasks)

**路由前缀**: `/tasks`

#### GET /tasks/

获取任务列表。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态筛选 |
| type | string | 类型筛选 |
| limit | int | 数量限制 |

---

#### GET /tasks/stats

获取任务统计。

**响应**:

```json
{
  "failed_process_tasks": 5
}
```

---

#### GET /tasks/status

获取全局任务状态（扫描状态、快速模式等）。

---

#### GET /tasks/grouped-status

按状态分组统计任务。

---

#### POST /tasks/fast-mode

设置快速模式。

**请求体**:

```json
{
  "enabled": true
}
```

---

#### POST /tasks/categories/{category}/pause

暂停指定分类的任务。

---

#### POST /tasks/categories/{category}/resume

恢复指定分类的任务。

---

#### GET /tasks/{task_id}

获取任务详情。

---

#### POST /tasks/

创建新任务。

**请求体**:

```json
{
  "type": "SCAN_FOLDER | PROCESS_IMAGE | ...",
  "payload": {}
}
```

**任务类型**:
- `SCAN_FOLDER`: 扫描文件夹
- `PROCESS_IMAGE`: 处理图片
- `EXTRACT_METADATA`: 提取元数据
- `RECOGNIZE_FACE`: 人脸识别
- `OCR`: 文字识别
- `CLASSIFY_IMAGE`: 图片分类
- `VISUAL_DESCRIPTION`: 视觉描述
- `RECOGNIZE_TICKET`: 票据识别
- `SIMILAR_PHOTO_CLUSTERING`: 相似照片聚类

---

#### POST /tasks/{task_id}/cancel

取消任务。

---

#### POST /tasks/{task_id}/retry

重试失败的任务。

---

#### POST /tasks/retry-all-failed

重试所有失败任务。

**查询参数**: `types` - 任务类型列表

---

#### DELETE /tasks/failed

删除所有失败任务。

---

### 设置模块 (Settings)

**路由前缀**: `/settings`

#### GET /settings/

获取当前用户的所有设置。

---

#### PUT /settings/

更新设置。

**请求体**: 设置对象（部分更新）

---

#### GET /settings/storage-root

获取存储根目录。

---

#### PUT /settings/storage-root

更新存储根目录。

**请求体**:

```json
{
  "storage_root": "/path/to/photos"
}
```

---

#### GET /settings/directories

获取目录列表（主目录 + 外部目录）。

---

#### POST /settings/directories

添加外部目录。

**请求体**:

```json
{
  "path": "/path/to/external/photos",
  "user_id": "UUID?"
}
```

---

#### DELETE /settings/directories

移除外部目录（同时删除关联照片）。

---

#### POST /settings/filter/apply

应用过滤规则（后台任务）。

---

#### GET /settings/export

导出设置。

---

#### POST /settings/import

导入设置。

---

#### 地图数据接口

##### GET /settings/map/countries

获取支持的国家列表。

##### GET /settings/map/downloaded

获取已下载的国家数据。

##### POST /settings/map/download

下载国家地图数据（后台任务）。

**请求体**:

```json
{
  "code": "CN"
}
```

##### POST /settings/map/upload

上传地图数据文件（CSV 格式）。

##### GET /settings/map/files/{filename}

下载地图数据文件。

##### DELETE /settings/map/files/{filename}

删除地图数据文件。

---

### 统计模块 (Stats)

**路由前缀**: `/stats`

#### GET /stats/dashboard

获取仪表盘数据。

**响应**:

```json
{
  "total_photos": 10000,
  "total_videos": 500,
  "total_size": "50GB",
  "photos_this_month": 100,
  "storage_used": "50GB"
}
```

---

#### GET /stats/timeline

获取时间轴统计数据。

**查询参数**: 支持多种筛选条件

---

#### GET /stats/heatmap

获取热力图数据。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| year | int | 年份筛选 |

---

#### GET /stats/filters

获取筛选器选项（所有可用的筛选值）。

---

### 智能分类模块 (Classification)

**路由前缀**: `/classification`

#### GET /classification

获取智能分类标签列表。

**响应**: 每个标签包含封面图片和照片数量

---

#### GET /classification/{path:path}/photos

获取分类下的照片列表。

**说明**: `path` 支持多级标签（包含 `/`）

---

### 火车票模块 (Train Ticket)

**路由前缀**: `/train-tickets`

#### POST /train-tickets/recognize

识别车票图片。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | 车票图片 |

**响应**: 识别出的结构化数据

```json
{
  "train_code": "G1234",
  "departure_station": "北京南",
  "arrival_station": "上海虹桥",
  "datetime": "2025-01-01T08:00",
  "seat_num": "12A",
  "seat_type": "二等座",
  "price": 553.0,
  "name": "张三"
}
```

---

#### POST /train-tickets/import

批量导入车票数据（支持 JSON/CSV）。

**请求体**: `multipart/form-data`

| 字段 | 类型 | 说明 |
|------|------|------|
| file | File | 数据文件（最大 10MB）|

---

#### GET /train-tickets/export

导出车票数据。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| format | string | 格式：json / csv |

---

#### GET /train-tickets

获取车票列表。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| skip | int | 偏移量 |
| limit | int | 数量（1-100）|
| train_code | string | 车次号（模糊匹配）|
| name | string | 乘车人（模糊匹配）|
| departure_station | string | 出发站（模糊匹配）|
| arrival_station | string | 到达站（模糊匹配）|
| start_datetime | datetime | 发车时间起始 |
| end_datetime | datetime | 发车时间结束 |

---

#### POST /train-tickets

创建车票记录。

---

#### GET /train-tickets/{ticket_id}

获取车票详情。

---

#### PUT /train-tickets/{ticket_id}

更新车票信息。

---

#### DELETE /train-tickets/{ticket_id}

删除车票记录。

---

### 索引模块 (Index)

**路由前缀**: `/index`

#### POST /index/rebuild

重建索引（重新扫描所有照片）。

---

#### GET /index/status

获取扫描状态。

---

#### GET /index/logs

获取索引日志。

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| limit | int | 数量限制，默认 100 |

---

## 附录

### 数据库结构

TrailSnap 使用 PostgreSQL 数据库，并启用 pgvector 扩展支持向量搜索。以下是所有数据表的详细结构。

#### 数据库架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              核心实体关系图                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐       ┌──────────┐       ┌──────────────────┐               │
│   │  users   │───1:N─│  photos  │───1:1──│ photo_metadata   │               │
│   └──────────┘       └──────────┘       └──────────────────┘               │
│        │                  │                       │                         │
│        │                  │                       │                         │
│        │             ┌────┴────┐                  │                         │
│        │             │         │                  │                         │
│        │         ┌───┴───┐ ┌───┴───┐              │                         │
│        │         │ faces │ │  ocr  │              │                         │
│        │         └───┬───┘ └───────┘              │                         │
│        │             │                            │                         │
│        │         ┌───┴──────────┐                 │                         │
│        │         │face_identities│◄───────────────┘                         │
│        │         └──────────────┘                                           │
│        │                                                                    │
│        │         ┌──────────┐       ┌───────────────┐                      │
│        └─────1:N─│  albums  │──M:N──│ album_photos  │                      │
│                  └──────────┘       └───────────────┘                      │
│                                            │                                │
│                                            │                                │
│                                       ┌────┴────┐                          │
│                                       │  photos │                          │
│                                       └─────────┘                          │
│                                                                            │
│   ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│   │agent_sessions│──1:N│agent_messages  │    │ image_vectors   │           │
│   └──────────────┘    └─────────────────┘    └─────────────────┘           │
│                                                                            │
│   ┌──────────────┐    ┌───────────────┐    ┌─────────────────┐            │
│   │    tasks     │    │ train_tickets │    │flight_tickets   │            │
│   └──────────────┘    └───────────────┘    └─────────────────┘            │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

#### users - 用户表

存储系统用户信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, INDEX | 用户唯一标识 |
| username | String | UNIQUE, INDEX | 用户名 |
| email | String | UNIQUE, INDEX | 邮箱地址 |
| hashed_password | String | NOT NULL | 密码哈希值 |
| is_active | Boolean | DEFAULT TRUE | 账户是否激活 |
| is_superuser | Boolean | DEFAULT FALSE | 是否为超级管理员 |
| failed_login_attempts | Integer | DEFAULT 0 | 登录失败次数 |
| last_failed_login | DateTime | NULL | 最后一次登录失败时间 |
| lockout_until | DateTime | NULL | 账户锁定截止时间 |
| security_question | String | NULL | 密保问题 |
| security_answer_hash | String | NULL | 密保答案哈希 |
| settings | JSON | DEFAULT {} | 用户设置（存储路径、AI配置等）|

**索引**:
- `idx_users_username` on `username`
- `idx_users_email` on `email`

---

#### photos - 照片表

存储照片/视频的基本信息，是系统的核心实体。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 照片唯一标识 |
| filename | String(255) | - | 文件名 |
| file_path | String(255) | NOT NULL | 文件存储路径 |
| file_type | Enum | NOT NULL | 文件类型：`image`, `video`, `live_photo` |
| photo_time | DateTime | INDEX | 拍摄时间（从 EXIF 提取）|
| upload_time | DateTime | DEFAULT NOW | 上传时间 |
| size | BigInteger | - | 文件大小（字节）|
| width | Integer | - | 图片宽度（像素）|
| height | Integer | - | 图片高度（像素）|
| duration | Float | DEFAULT 0 | 视频/动图时长（秒）|
| image_type | Enum | - | 图片来源：`Screenshot`, `Camera`, `Other` |
| processed_tasks | JSON | DEFAULT {} | 任务处理状态跟踪 |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |

**processed_tasks 示例**:
```json
{
  "thumbnail": true,
  "metadata": true,
  "face": false,
  "ocr": true,
  "classify": true
}
```

**关联关系**:
- `albums`: M:N → albums（通过 album_photos）
- `metadata_info`: 1:1 → photo_metadata
- `faces`: 1:N → faces
- `image_description`: 1:1 → image_descriptions
- `tags`: M:N → photo_tags（通过 photo_tag_relations）

---

#### photo_metadata - 照片元数据表

存储照片的 EXIF 信息和地理位置数据。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| photo_id | UUID | PK, FK → photos.id | 关联照片 ID |
| exif_info | Text | - | 原始 EXIF 信息（文本格式）|
| longitude | DECIMAL(10,7) | - | 经度 |
| latitude | DECIMAL(10,7) | - | 纬度 |
| city | String(100) | - | 城市 |
| district | String(100) | - | 区/县 |
| province | String(100) | - | 省份 |
| country | String(100) | - | 国家 |
| address | Text | - | 详细地址 |
| make | String(100) | - | 相机品牌（如 Apple、Canon）|
| model | String(100) | - | 相机型号（如 iPhone 15 Pro）|
| shooting_params | JSON | - | 拍摄参数（光圈、快门、ISO 等）|
| location_api | String(255) | - | 位置信息来源 API |
| scene_id | UUID | FK → scenes.id | 关联景区 ID |

**索引**:
- `idx_location_lat_lng` on `(latitude, longitude)`
- `idx_location_city` on `city`
- `idx_location_province` on `province`
- `idx_location_country` on `country`

**shooting_params 示例**:
```json
{
  "aperture": "f/1.8",
  "shutter_speed": "1/120",
  "iso": 64,
  "focal_length": "6.86mm"
}
```

---

#### albums - 相册表

存储相册信息，支持三种类型：普通相册、条件相册、智能相册。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 相册唯一标识 |
| name | String(100) | NOT NULL | 相册名称 |
| description | Text | - | 相册描述 |
| type | String(20) | NOT NULL, DEFAULT 'user' | 相册类型 |
| condition | JSON | - | 筛选条件（条件相册）|
| query_embedding | Vector(512) | - | 查询向量（智能相册）|
| threshold | Float | DEFAULT 0.25 | 相似度阈值（智能相册）|
| num_photos | Integer | DEFAULT 0 | 照片数量 |
| cover_id | UUID | FK → photos.id | 封面照片 ID |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| create_time | DateTime | DEFAULT NOW | 创建时间 |

**相册类型说明**:
- `normal` / `user`: 普通相册，手动添加照片
- `conditional`: 条件相册，根据条件自动筛选（如时间范围、地点）
- `smart`: 智能相册，根据描述通过 AI 向量搜索匹配

---

#### album_photos - 相册-照片关联表

多对多关系中间表。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| album_id | UUID | FK → albums.id, NOT NULL | 相册 ID |
| photo_id | UUID | FK → photos.id, NOT NULL | 照片 ID |
| created_at | DateTime | DEFAULT NOW | 添加时间 |

**约束**:
- `uq_album_photo`: UNIQUE(album_id, photo_id)

---

#### album_shared_users - 相册共享用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| album_id | UUID | PK, FK → albums.id | 相册 ID |
| user_id | UUID | PK, FK → users.id | 用户 ID |
| created_at | DateTime | DEFAULT NOW | 共享时间 |

---

#### faces - 人脸表

存储检测到的人脸信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| photo_id | UUID | FK → photos.id, NOT NULL | 所属照片 ID |
| face_identity_id | UUID | FK → face_identities.id | 关联人物 ID |
| face_feature | VECTOR(512) | - | 人脸特征向量（512 维）|
| face_rect | JSON | - | 人脸检测框 [x1, y1, x2, y2] |
| face_confidence | DECIMAL(5,4) | - | 检测置信度 |
| recognize_confidence | DECIMAL(5,4) | - | 识别置信度 |
| create_time | DateTime | DEFAULT NOW | 创建时间 |
| update_time | DateTime | ON UPDATE | 更新时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除标记 |

**索引**:
- `idx_face_photo_id` on `photo_id`
- `idx_face_identity_id` on `face_identity_id`
- `idx_face_feature` on `face_feature` (HNSW 向量索引，余弦距离)

**向量索引说明**:
使用 pgvector 的 HNSW 索引，支持高效的余弦相似度搜索：
```sql
CREATE INDEX idx_face_feature ON faces
USING hnsw (face_feature vector_cosine_ops);
```

---

#### face_identities - 人物表

存储识别出的人物身份信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 人物唯一标识 |
| identity_name | String(500) | - | 人物名称 |
| description | String(500) | - | 人物描述 |
| tags | JSON | - | 标签列表 |
| default_face_id | Integer | FK → faces.id | 默认封面人脸 ID |
| create_time | DateTime | DEFAULT NOW | 创建时间 |
| update_time | DateTime | ON UPDATE | 更新时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除标记 |
| is_hidden | Boolean | DEFAULT FALSE | 是否隐藏 |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |

---

#### image_vectors - 图像向量表

存储照片的 CLIP 图像向量，用于语义搜索。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| photo_id | UUID | PK, FK → photos.id | 关联照片 ID |
| embedding | Vector(512) | - | CLIP 图像向量（512 维）|
| model_name | String | DEFAULT 'clip-ViT-B-32' | 向量模型名称 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

**说明**:
- 使用 CLIP ViT-B/32 模型生成 512 维向量
- 支持文本-图像跨模态搜索

---

#### image_descriptions - 图像描述表

存储 AI 生成的照片描述和评分。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO, INDEX | 自增主键 |
| photo_id | UUID | FK → photos.id, NOT NULL, INDEX | 关联照片 ID |
| description | Text | - | 图片描述 |
| memory_score | Float | - | 回忆价值评分（0-100）|
| quality_score | Float | - | 图片质量评分（0-100）|
| tags | JSON | - | AI 识别的标签列表 |
| reason | Text | - | 评分原因说明 |
| narrative | Text | - | 一句话文案 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

**tags 示例**:
```json
["人物", "户外", "日落", "海滩"]
```

---

#### ocr_results - OCR 识别结果表

存储照片中识别出的文字信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| photo_id | UUID | FK → photos.id, NOT NULL, INDEX | 关联照片 ID |
| text | String | INDEX | 识别的文字内容 |
| text_score | Float | - | 识别置信度 |
| polygon | JSON | - | 文字区域多边形坐标 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| updated_at | DateTime | ON UPDATE | 更新时间 |

**polygon 格式**:
```json
[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
```
坐标已归一化到 0-1 范围。

---

#### photo_tags - 标签表

存储照片标签定义。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 标签唯一标识 |
| tag_name | String(50) | NOT NULL | 标签名称 |
| type | String(50) | - | 标签类型 |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| create_time | DateTime | DEFAULT NOW | 创建时间 |
| update_time | DateTime | ON UPDATE | 更新时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除标记 |

---

#### photo_tag_relations - 照片-标签关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| photo_id | UUID | FK → photos.id, NOT NULL | 照片 ID |
| tag_id | UUID | FK → photo_tags.id, NOT NULL | 标签 ID |
| confidence | Float | DEFAULT 1.0 | 置信度 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| is_deleted | Boolean | DEFAULT FALSE | 软删除标记 |

**约束**:
- `uq_photo_tag`: UNIQUE(photo_id, tag_id)

---

#### scenes - 景区表

存储景区/景点信息，支持自定义景区。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 景区唯一标识 |
| name | String(255) | NOT NULL | 景区名称 |
| description | Text | - | 景区描述 |
| level | Integer | - | 景区等级（5A、4A 等）|
| address | Text | - | 详细地址 |
| latitude | DECIMAL(10,7) | - | 中心纬度 |
| longitude | DECIMAL(10,7) | - | 中心经度 |
| radius | Integer | - | 覆盖半径（米）|
| polygon | JSON | - | 多边形边界坐标 |
| is_custom | Boolean | DEFAULT TRUE | 是否为用户自定义 |
| owner_id | UUID | FK → users.id, INDEX | 创建者 ID |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

**polygon 格式**:
```json
[[lng1, lat1], [lng2, lat2], [lng3, lat3], ...]
```

---

#### tasks - 任务表

存储后台任务信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 任务唯一标识 |
| type | String(50) | NOT NULL | 任务类型 |
| status | String(20) | DEFAULT 'pending' | 任务状态 |
| priority | Integer | DEFAULT 0 | 优先级（数值越大优先级越高）|
| payload | JSON | - | 任务参数 |
| result | JSON | - | 任务结果 |
| error | Text | - | 错误信息 |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| total_items | Integer | DEFAULT 0 | 总项目数 |
| processed_items | Integer | DEFAULT 0 | 已处理项目数 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| updated_at | DateTime | ON UPDATE | 更新时间 |

**任务状态 (TaskStatus)**:
| 状态 | 说明 |
|------|------|
| pending | 等待处理 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

**任务类型 (TaskType)**:
| 类型 | 说明 |
|------|------|
| SCAN_FOLDER | 扫描文件夹 |
| PROCESS_BASIC | 基础处理（缩略图、预览）|
| PROCESS_IMAGE | 完整图片处理（已弃用）|
| GENERATE_THUMBNAIL | 生成缩略图 |
| EXTRACT_METADATA | 提取元数据和地理位置 |
| CLASSIFY_IMAGE | 图片分类 |
| RECOGNIZE_FACE | 人脸识别 |
| RECOGNIZE_TICKET | 票据识别 |
| REBUILD_THUMBNAILS | 重建缩略图 |
| REBUILD_METADATA | 重建元数据 |
| OCR | 文字识别 |
| VISUAL_DESCRIPTION | 视觉描述生成 |
| SIMILAR_PHOTO_CLUSTERING | 相似照片聚类 |

---

#### agent_sessions - 智能助手会话表

存储 AI 助手的对话会话。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, INDEX | 会话唯一标识 |
| user_id | UUID | FK → users.id, INDEX, NOT NULL | 所属用户 ID |
| title | String(255) | - | 会话标题 |
| status | String(50) | DEFAULT 'active' | 会话状态 |
| context_summary | Text | - | 上下文摘要 |
| summary_update_time | DateTime | - | 摘要更新时间 |
| is_pinned | Boolean | DEFAULT FALSE | 是否置顶 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

---

#### agent_messages - 智能助手消息表

存储会话中的消息记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| session_id | UUID | FK → agent_sessions.id, INDEX, NOT NULL | 所属会话 ID |
| role | String(50) | NOT NULL | 角色：user/assistant/system |
| content | Text | NOT NULL | 消息内容 |
| content_type | String(50) | DEFAULT 'text' | 内容类型 |
| content_ext | JSON | - | 扩展内容（如图片引用）|
| token_count | Integer | DEFAULT 0 | Token 数量 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

---

#### agent_tokens - API 访问令牌表

存储第三方应用访问令牌。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, INDEX | 令牌唯一标识 |
| user_id | UUID | FK → users.id, INDEX, NOT NULL | 所属用户 ID |
| name | String | NOT NULL | 令牌名称 |
| token | String | UNIQUE, INDEX, NOT NULL | 令牌值（以 ts_ 开头）|
| created_at | DateTime | NOT NULL | 创建时间 |
| expires_at | DateTime | NOT NULL | 过期时间 |
| is_deleted | Boolean | DEFAULT FALSE | 是否已删除 |

---

#### train_tickets - 火车票表

存储火车票信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | String(36) | PK, INDEX | 票据 ID（UUID 格式）|
| train_code | String(20) | INDEX, NOT NULL | 车次号（如 G1920）|
| departure_station | String(50) | NOT NULL | 出发站 |
| arrival_station | String(50) | NOT NULL | 到达站 |
| date_time | DateTime | NOT NULL | 发车时间 |
| carriage | String(10) | NOT NULL | 车厢号 |
| seat_num | String(10) | NOT NULL | 座位号 |
| berth_type | String(10) | DEFAULT '无' | 铺位类型（上/中/下/无）|
| price | Numeric(10,2) | NOT NULL | 票价 |
| seat_type | String(20) | NOT NULL | 座位类型（一等座/二等座等）|
| name | String(50) | NOT NULL | 乘车人姓名 |
| discount_type | String(20) | DEFAULT '全价票' | 优惠类型 |
| total_mileage | DECIMAL(10,1) | DEFAULT 0 | 线路里程（公里）|
| total_running_time | Integer | DEFAULT 0 | 运行时间（分钟）|
| stop_stations | Text | DEFAULT '[]' | 经停站列表（JSON 格式）|
| comments | Text | - | 备注 |
| photo_id | String(36) | INDEX | 关联照片 ID |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| updated_at | DateTime | ON UPDATE | 更新时间 |

---

#### flight_tickets - 机票表

存储机票信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | String(36) | PK, INDEX | 票据 ID（UUID 格式）|
| flight_code | String(20) | INDEX, NOT NULL | 航班号 |
| departure_city | String(50) | NOT NULL | 出发城市 |
| arrival_city | String(50) | NOT NULL | 到达城市 |
| date_time | DateTime | NOT NULL | 出发时间 |
| price | Numeric(10,2) | NOT NULL | 票价 |
| name | String(50) | NOT NULL | 乘客姓名 |
| total_mileage | DECIMAL(10,1) | DEFAULT 0 | 里程（公里）|
| total_running_time | Integer | DEFAULT 0 | 飞行时长（分钟）|
| comments | Text | - | 备注 |
| photo_id | String(36) | INDEX | 关联照片 ID |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| created_at | DateTime | DEFAULT NOW | 创建时间 |
| updated_at | DateTime | ON UPDATE | 更新时间 |

---

#### image_clusters - 图像聚类表

存储相似照片聚类结果。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| cluster_id | UUID | PK | 聚类唯一标识 |
| task_id | String(255) | - | 关联任务 ID |
| cluster_type | String(50) | NOT NULL | 聚类类型（SIMILARITY）|
| count | Integer | DEFAULT 0 | 聚类内照片数量 |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

---

#### photo_clusters - 照片-聚类关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| photo_id | UUID | FK → photos.id, NOT NULL | 照片 ID |
| cluster_id | UUID | FK → image_clusters.cluster_id, NOT NULL | 聚类 ID |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

---

#### index_logs - 索引日志表

存储照片索引操作日志。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, AUTO | 自增主键 |
| action | String(50) | NOT NULL | 操作类型（created/deleted/updated）|
| file_path | Text | NOT NULL | 文件路径 |
| photo_id | UUID | - | 关联照片 ID |
| details | Text | - | 详细信息 |
| owner_id | UUID | FK → users.id, INDEX | 所属用户 ID |
| created_at | DateTime | DEFAULT NOW | 创建时间 |

---

#### system_state - 系统状态表

存储系统级别的键值对配置。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| key | String | PK, INDEX | 配置键 |
| value | Text | - | 配置值（JSON 字符串）|

---

### 数据库关系总结

```
users (1) ──────< (N) photos
  │                    │
  │                    ├──< (1:1) photo_metadata ────< (N:1) scenes
  │                    │
  │                    ├──< (1:N) faces ────> (N:1) face_identities
  │                    │
  │                    ├──< (1:1) image_vectors
  │                    │
  │                    ├──< (1:1) image_descriptions
  │                    │
  │                    ├──< (1:N) ocr_results
  │                    │
  │                    └──< (M:N) photo_tags (via photo_tag_relations)
  │
  ├──< (N) albums ────< (M:N) photos (via album_photos)
  │
  ├──< (N) agent_sessions ────< (N) agent_messages
  │
  ├──< (N) agent_tokens
  │
  ├──< (N) tasks
  │
  ├──< (N) train_tickets
  │
  ├──< (N) flight_tickets
  │
  └──< (N) index_logs
```

### 向量索引说明

TrailSnap 使用 pgvector 扩展支持向量搜索，主要涉及以下向量字段：

| 表名 | 字段 | 维度 | 用途 | 索引类型 |
|------|------|------|------|----------|
| image_vectors | embedding | 512 | 图像语义搜索 | HNSW (余弦距离) |
| faces | face_feature | 512 | 人脸相似度搜索 | HNSW (余弦距离) |
| albums | query_embedding | 512 | 智能相册查询 | - |

### 错误码参考

| 错误信息 | 说明 |
|----------|------|
| Token has expired | Token 已过期，需重新登录 |
| Could not validate credentials | Token 无效 |
| User not found | 用户不存在 |
| Album not found | 相册不存在 |
| Photo not found | 照片不存在 |
| Identity not found | 人物不存在 |
| Scene not found | 景区不存在 |
| Session not found | 会话不存在 |
| Task not found | 任务不存在 |
| Not authorized | 权限不足 |
| Invalid task type | 无效的任务类型 |
| AI Service error | AI 服务调用失败 |

---

## 更新日志

- **v0.3.1**: 添加智能助手流式对话、令牌管理功能
- **v0.3.0**: 添加年度报告、那年今日功能
- **v0.2.x**: 基础照片管理、人脸识别、OCR 功能
