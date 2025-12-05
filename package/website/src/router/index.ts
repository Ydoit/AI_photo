// src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

// 路由懒加载（优化首屏性能，TS 自动推断类型）
const HomePage = () => import('@/views/HomePage.vue');
// const AlbumPage = () => import('@/views/AlbumPage.vue');
const AlbumList = () => import('@/views/AlbumList.vue');
const AlbumDetail = () => import('@/views/AlbumDetail.vue');
const PhotosPage = () => import('@/views/PhotosPage.vue');
const TicketPage = () => import('@/views/TicketPage.vue');
const StatisticsPage = () => import('@/views/StatisticsPage.vue');
const More = () => import('@/views/More.vue');
const Responsive = () => import('@/views/tools/Responsive.vue');
const ToolPage = () => import('@/views/tools/ToolPage.vue');

const NotFound = () => import('@/views/NotFound.vue');
const AboutPage = () => import('@/views/AboutPage.vue');

// 路由配置：TS 类型为 RouteRecordRaw 数组，强制类型校验
const routes: RouteRecordRaw[] = [
  // 主布局组：所有子页面都使用 MainLayout
  {
    path: '/',
    component: () => import('@/components/RouteOutlet.vue'),
    meta: { layout: 'main' }, // 标记布局类型（供 App.vue 识别）
    children: [
      { path: '', name: 'Home', component: HomePage, meta: { title: '首页' } },
      { path: '/album', name: 'AlbumList', component: AlbumList, meta: { title: 'AI相册' } },
      { path: '/album/:id', name: 'AlbumDetail', component: AlbumDetail, meta: { title: '相册详情' } },
      { path: '/photos', name: 'Photos', component: PhotosPage, meta: { title: '所有照片' } },
      { path: '/ticket', name: 'Ticket', component: TicketPage, meta: { title: '车票', keepAlive: true } },
      { path: '/statistics', name: 'Statistics', component: StatisticsPage, meta: { title: '统计' } },
      { path: '/tools', name: 'Tool', component: ToolPage, meta: { title: '工具' } },
      { path: '/tools/responsive', name: 'Responsive', component: Responsive, meta: { title: '响应式测试' } },
      { path: '/more', name: 'More', component: More, meta: { title: '更多' } },
      { path: '/about', name: 'About', component: AboutPage, meta: { title: '关于' } }, // 新增 About 路由
    ],
  },

  // 404 页面（使用空白布局）
  {
    path: '/:pathMatch(.*)*', // 匹配所有未定义路由
    name: 'NotFound',
    component: NotFound,
    meta: { layout: 'blank', title: '页面未找到' },
  },
];

// 创建路由实例
const router = createRouter({
  //history: createWebHistory(import.meta.env.BASE_URL), // 读取环境变量中的基础路径
  history: createWebHistory(),
  routes,
  // 可选：路由切换时滚动到顶部
  scrollBehavior: () => ({ top: 0 }),
});

// 可选：路由守卫 - 动态设置页面标题
router.beforeEach((to) => {
  if (to.meta.title) {
    document.title = to.meta.title as string;
  }
});

export default router;