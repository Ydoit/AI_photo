import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "TrailSnap 行影集",
  description: "AI 驱动的智能相册与旅行足迹记录工具",
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '用户指南', link: '/docs/guide/user' },
      { text: '开发者文档', link: '/docs/dev/guide' }
    ],

    sidebar: {
      '/docs/guide/': [
        {
          text: '用户指南',
          items: [
            { text: '使用简介', link: '/docs/guide/user' }
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
      { icon: 'github', link: 'https://github.com/your-repo/trailsnap' }
    ],

    footer: {
      message: '基于 MIT 许可发布',
      copyright: '版权所有 © 2024-至今 TrailSnap 贡献者'
    }
  }
})
