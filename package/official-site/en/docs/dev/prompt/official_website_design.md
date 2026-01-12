# TrailSnap Official Website Design Document

## 1. Website Function Introduction

The TrailSnap official website aims to provide a platform for users and developers to fully understand, use, and participate in the TrailSnap project. The website mainly features the following functions:

- **Landing Page**: Through a modern landing page, showcase TrailSnap's core features (AI albums, smart classification, footprint map, ticket recognition, etc.) to attract users to try it.
- **User Documentation**: Provide detailed user operation guides to help ordinary users get started quickly, understand how to import photos, manage albums, and use AI features.
- **Developer Documentation**: Provide architecture design, technology stack analysis, environment setup, and deployment guides for contributors and secondary developers.
- **FAQ**: Summarize problems and solutions that users may encounter during use.
- **Version Updates**: Showcase the project's changelog and future plans.

## 2. Website Documentation Structure

The website documentation is built based on VitePress, and the content is derived from existing design documents in the project's `doc` directory and structured.

### 2.1 Architecture Design Document
- **Content Source**: `doc/architecture_design.md`
- **Main Content**:
  - Overall Architecture Diagram (Mermaid)
  - Frontend and Backend Separation Architecture Description
  - AI Microservice Interaction Flow
  - Technology Selection and Version (Frontend, Backend, AI, Database)
  - Directory Structure Description

### 2.2 Frontend Framework Analysis
- **Content Source**: `doc/frontend_analysis.md`
- **Main Content**:
  - Technology Stack Breakdown (Vue 3, TypeScript, Vite, Element Plus, TailwindCSS, Pinia)
  - Component Hierarchy Diagram
  - Performance Metrics and Optimization Analysis
  - Frontend and Backend Interaction Diagram

### 2.3 Backend Framework Analysis
- **Content Source**: `doc/backend_analysis.md`
- **Main Content**:
  - Core Framework Description (FastAPI, Uvicorn, SQLAlchemy, Alembic)
  - Service Module Division and Call Relationship Diagram
  - AI Microservice Call Chain
  - API Design Specification and Status

### 2.4 Developer Guide
- **Content Source**: `doc/developer_guide.md`
- **Main Content**:
  - Environment Preparation (Node.js, Python, PostgreSQL, Docker)
  - Local Development Environment Setup Steps
  - Database Migration Guide
  - Code Specifications and Contribution Guide

### 2.5 User Guide
- **Content Source**: `doc/user_guide.md`
- **Main Content**:
  - System Login and Initialization
  - Photo Upload and Management
  - Smart Classification and Search
  - Footprint Map Usage
  - Ticket Recognition and Journey Management
  - Annual Report Generation

### 2.6 FAQ
- **Content Planning**:
  - Common Deployment Errors (Docker port conflicts, database connection failures)
  - AI Model Download Failure Handling
  - Browser Compatibility Description
  - Data Backup and Recovery

## 3. Deployment Plan

### 3.1 Deployment Platform
- **GitHub Pages**: Utilize GitHub's free static hosting service and achieve automated deployment through GitHub Actions.

### 3.2 Automated Deployment Process
Trigger GitHub Actions Workflow every time code is pushed to the `main` branch, performing the following steps:
1. **Checkout**: Pull the latest code.
2. **Setup Node**: Configure the Node.js environment.
3. **Install Dependencies**: Install VitePress and related dependencies.
4. **Build**: Run `vitepress build` to generate static files.
5. **Deploy**: Push the generated static files (`dist` directory) to the `gh-pages` branch.

## 4. Directory Structure Planning

The website code will be stored in the `package/official-site` directory, keeping the Monorepo structure clean.

```
package/official-site/
├── .vitepress/
│   ├── config.mts       # VitePress configuration file (navbar, sidebar, theme config)
│   └── theme/           # Custom theme styles
├── docs/                # Documentation content (Markdown)
│   ├── guide/           # User guide
│   │   ├── intro.md
│   │   └── ...
│   ├── dev/             # Developer documentation
│   │   ├── architecture.md
│   │   ├── frontend.md
│   │   └── backend.md
│   └── public/          # Static resources (images)
├── index.md             # Landing Page
└── package.json         # Dependency configuration
```
