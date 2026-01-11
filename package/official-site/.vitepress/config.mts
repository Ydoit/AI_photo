import { defineConfig } from 'vitepress'
import { withMermaid } from "vitepress-plugin-mermaid";
export default withMermaid(defineConfig({
  base: '/',
  title: "TrailSnap 行影集",
  description: "AI 驱动的智能相册与旅行足迹记录工具",
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }]
  ],
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '功能演示', link: '/docs/guide/demo' },
      { text: '用户指南', link: '/docs/guide/install' },
      { text: '开发者文档', link: '/docs/dev/guide' },
      { text: '博客', link: '/docs/blog/' },
      { text: '问题反馈', link: '/docs/guide/feedback' }
    ],
    search: {
      provider: 'local'
    },

    sidebar: {
      '/docs/guide/': [
        {
          text: '用户指南',
          items: [
            { text: '概览', link: '/docs/guide/overview' },
            { text: '安装指南', link: '/docs/guide/install' },
            {
              text: 'Docker 部署',
              collapsible: true,
              collapsed: true,
              items: [
                { text: '通用部署', link: '/docs/guide/docker/' },
                { text: '绿联 NAS', link: '/docs/guide/docker/ugreen' },
                { text: '极空间', link: '/docs/guide/docker/zspace' },
                { text: '飞牛OS', link: '/docs/guide/docker/fnos' }
              ]
            },
            { text: '使用简介', link: '/docs/guide/user' },
            {
              text: '设置指南',
              link: '/docs/guide/settings/',
              collapsible: true,
              collapsed: true,
              items: [
                { text: '地图设置', link: '/docs/guide/settings/mapsetting' }
              ]
            },
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
            { text: '任务管理设计', link: '/docs/dev/task_manager' },
            {
              text: 'AI提示词',
              link: '/docs/dev/prompt',
              collapsible: true,
              collapsed: false,
              items: [
                { text: '2025-12-25', link: '/docs/dev/prompt/2025-12-25' },
                { text: '2026-01-07', link: '/docs/dev/prompt/2026-01-07' },
                { text: '官网设计文档', link: '/docs/dev/prompt/official_website_design' }
              ]
            }
          ]
        }
      ],
      '/docs/blog/': [
        {
          text: '博客',
          items: [
            { text: '文章列表', link: '/docs/blog/' },
            { text: '功能全景速览', link: '/docs/blog/feature-scan' },
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
}))
