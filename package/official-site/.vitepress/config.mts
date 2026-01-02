import { defineConfig } from 'vitepress'

export default defineConfig({
  base: '/',
  title: "TrailSnap 行影集",
  description: "AI 驱动的智能相册与旅行足迹记录工具",
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '用户指南', link: '/docs/guide/install' },
      { text: '开发者文档', link: '/docs/dev/guide' },
      { text: '问题反馈', link: '/docs/guide/feedback' }
    ],

    sidebar: {
      '/docs/guide/': [
        {
          text: '用户指南',
          items: [
            { text: '安装指南', link: '/docs/guide/install' },
            { text: '使用简介', link: '/docs/guide/user' },
            { text: '问题反馈', link: '/docs/guide/feedback' }
          ]
        }
      ],
      '/docs/dev/': [
        {
          text: '开发者指南',
          items: [
            { text: '快速开始', link: '/docs/dev/guide' },
            { text: '架构设计', link: '/docs/dev/architecture' },
            { text: '前端分析', link: '/docs/dev/frontend' },
            { text: '后端分析', link: '/docs/dev/backend' },
            { text: '任务管理设计', link: '/docs/dev/task_manager' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/LC044/TrailSnap' }
    ],

    outline: {
      label: '页面导航'
    },
    
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '回到顶部',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    
    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    footer: {
      message: '基于 AGPL-3.0 许可发布',
      copyright: '版权所有 © 2025-至今 TrailSnap'
    }
  }
})
