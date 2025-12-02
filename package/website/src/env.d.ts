// src/env.d.ts
/// <reference types="vite/client" />

// 扩展 ImportMeta 接口，告诉 TS import.meta 包含 env 属性
interface ImportMeta {
  env: ImportMetaEnv;
}

// 声明你用到的环境变量类型（和 .env 文件中的变量对应）
interface ImportMetaEnv {
  // 必须以 VITE_ 开头（Vite 只识别该前缀的环境变量）
  readonly VITE_API_BASE_URL: string;
  // 若有其他环境变量，继续添加（如 VITE_APP_TITLE、VITE_DEBUG 等）
  // readonly VITE_APP_TITLE: string;
  // readonly VITE_DEBUG: boolean;
}