import 'mingcute_icon/font/Mingcute.css';
import { createApp } from 'vue'
import { createPinia } from 'pinia'  // 1. 导入 createPinia
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import './style.css'

import App from './App.vue'
import router from '@/router';
const app = createApp(App);
// 2. 创建 Pinia 实例
const pinia = createPinia()
app.use(pinia)  // 关键步骤：激活 Pinia
app.use(router);
app.use(ElementPlus)
app.mount('#app');


