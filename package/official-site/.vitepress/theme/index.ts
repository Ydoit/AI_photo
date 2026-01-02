import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import { useData } from 'vitepress'
import Comments from './components/Comments.vue'
import Home from './components/Home.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout() {
    const { frontmatter } = useData()
    return h(DefaultTheme.Layout, null, {
      // Hide comments on the custom home page
      'doc-after': () => frontmatter.value.home_custom ? null : h(Comments)
    })
  },
  enhanceApp({ app }: { app: any }) {
    app.component('Home', Home)
  }
}
