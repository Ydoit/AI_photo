// src/composables/useTheme.js

import { ref, watch, computed, provide, inject } from 'vue';

// ----------------- 主题配置 -----------------
export const themeColors = [
  { name: 'sky', label: '天空蓝', primary: '#1E88E5', secondary: '#64B5F6', rgb: '30, 136, 229' },
  { name: 'emerald', label: '森系绿', primary: '#10B981', secondary: '#34D399', rgb: '16, 185, 129' },
  { name: 'violet', label: '梦幻紫', primary: '#8B5CF6', secondary: '#A78BFA', rgb: '139, 92, 246' },
  { name: 'rose', label: '落日红', primary: '#F43F5E', secondary: '#FB7185', rgb: '244, 63, 94' },
  { name: 'amber', label: '复古橘', primary: '#F59E0B', secondary: '#FBBF24', rgb: '245, 158, 11' },
];

// 唯一的 Injection Key，防止冲突
const ThemeKey = Symbol('theme'); 

// ----------------- 核心逻辑 -----------------
export function useTheme() {
  const isDarkMode = ref(false);
  // 尝试从 localStorage 读取主题，否则默认天空蓝
  const savedThemeName = localStorage.getItem('theme-color') || 'sky';
  const initialTheme = themeColors.find(t => t.name === savedThemeName) || themeColors[0];
  const currentTheme = ref(initialTheme);

  // 1. 切换深色模式
  const toggleDarkMode = (val) => {
    isDarkMode.value = val;
    localStorage.setItem('theme-mode', val ? 'dark' : 'light');
  };

  // 2. 切换主题色
  const setTheme = (themeObj) => {
    currentTheme.value = themeObj;
    localStorage.setItem('theme-color', themeObj.name);
  };

  // 3. 全局副作用 (Watch Effect)
  watch(isDarkMode, (newVal) => {
    const root = document.documentElement;
    if (newVal) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, { immediate: true }); // 立即执行一次，读取初始化状态

  // 4. 计算 CSS 变量
  const themeStyle = computed(() => {
    return {
      '--theme-primary': currentTheme.value.primary,
      '--theme-rgb': currentTheme.value.rgb,
      '--text-color': isDarkMode.value ? '#ffffff' : '#1e293b'
    };
  });
  
  // 初始化时读取 localStorage 的深色模式状态
  if (localStorage.getItem('theme-mode') === 'dark') {
      isDarkMode.value = true;
  }

  return {
    isDarkMode,
    currentTheme,
    themeStyle,
    themeColors,
    toggleDarkMode,
    setTheme,
  };
}

// ----------------- Provider/Consumer Functions -----------------

// 根组件调用此函数来提供主题
export function provideTheme() {
  const theme = useTheme();
  provide(ThemeKey, theme);
  return theme;
}

// 任何子组件调用此函数来注入主题
export function injectTheme() {
  const theme = inject(ThemeKey);
  if (!theme) {
    console.error('Theme not provided. Did you call provideTheme() in the root component?');
  }
  return theme;
}