# TrailSnap 官网设计文档

## 1. 官网功能介绍

TrailSnap 官网旨在为用户和开发者提供一个全面了解、使用和参与 TrailSnap 项目的平台。官网主要具备以下功能：

- **项目展示 (Landing Page)**: 通过现代化的落地页，展示 TrailSnap 的核心功能（AI 相册、智能分类、足迹地图、票据识别等），吸引用户尝试。
- **用户文档**: 提供详细的用户操作指南，帮助普通用户快速上手，了解如何导入照片、管理相册、使用 AI 功能。
- **开发者文档**: 为贡献者和二次开发者提供架构设计、技术栈分析、环境搭建和部署指南。
- **常见问题 (FAQ)**: 汇总用户在使用过程中可能遇到的问题及解决方案。
- **版本更新**: 展示项目的更新日志和未来规划。

## 2. 官网文档结构

官网文档基于 VitePress 构建，文档内容来源于项目 `doc` 目录下的现有设计文档，并进行结构化整理。

### 2.1 架构设计文档
- **内容来源**: `doc/architecture_design.md`
- **主要内容**:
  - 整体架构图 (Mermaid)
  - 前后端分离架构说明
  - AI 微服务交互流程
  - 技术选型及版本 (Frontend, Backend, AI, Database)
  - 目录结构说明

### 2.2 前端框架分析
- **内容来源**: `doc/frontend_analysis.md`
- **主要内容**:
  - 技术栈拆解 (Vue 3, TypeScript, Vite, Element Plus, TailwindCSS, Pinia)
  - 组件层级关系图
  - 性能指标与优化分析
  - 前端与后端交互示意图

### 2.3 后端框架分析
- **内容来源**: `doc/backend_analysis.md`
- **主要内容**:
  - 核心框架说明 (FastAPI, Uvicorn, SQLAlchemy, Alembic)
  - 服务模块划分与调用关系图
  - AI 微服务调用链
  - API 设计规范与现状

### 2.4 开发者文档
- **内容来源**: `doc/developer_guide.md`
- **主要内容**:
  - 环境准备 (Node.js, Python, PostgreSQL, Docker)
  - 本地开发环境搭建步骤
  - 数据库迁移指南
  - 代码规范与贡献指南

### 2.5 用户指南
- **内容来源**: `doc/user_guide.md`
- **主要内容**:
  - 系统登录与初始化
  - 照片上传与管理
  - 智能分类与搜索
  - 足迹地图使用
  - 票据识别与行程管理
  - 年度报告生成

### 2.6 常见问题 (FAQ)
- **内容规划**:
  - 部署常见错误 (Docker 端口冲突, 数据库连接失败)
  - AI 模型下载失败处理
  - 浏览器兼容性说明
  - 数据备份与恢复

## 3. 部署方案

### 3.1 部署平台
- **GitHub Pages**: 利用 GitHub 提供的免费静态托管服务，通过 GitHub Actions 实现自动化部署。

### 3.2 自动化部署流程
每次代码推送到 `main` 分支时，触发 GitHub Actions Workflow，执行以下步骤：
1. **Checkout**: 拉取最新代码。
2. **Setup Node**: 配置 Node.js 环境。
3. **Install Dependencies**: 安装 VitePress 及相关依赖。
4. **Build**: 运行 `vitepress build` 生成静态文件。
5. **Deploy**: 将生成的静态文件 (`dist` 目录) 推送到 `gh-pages` 分支。

## 4. 目录结构规划

官网代码将存放于 `package/official-site` 目录下，保持 Monorepo 结构整洁。

```
package/official-site/
├── .vitepress/
│   ├── config.mts       # VitePress 配置文件 (导航栏, 侧边栏, 主题配置)
│   └── theme/           # 自定义主题样式
├── docs/                # 文档内容 (Markdown)
│   ├── guide/           # 用户指南
│   │   ├── intro.md
│   │   └── ...
│   ├── dev/             # 开发者文档
│   │   ├── architecture.md
│   │   ├── frontend.md
│   │   └── backend.md
│   └── public/          # 静态资源 (图片)
├── index.md             # 首页 (Landing Page)
└── package.json         # 依赖配置
```
