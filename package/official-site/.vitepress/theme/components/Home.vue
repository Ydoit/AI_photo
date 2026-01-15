<template>
  <div class="min-h-screen bg-white dark:bg-slate-900 text-neutral-dark dark:text-gray-100 font-sans overflow-x-hidden">
    
    <!-- 1. Navbar -->
    <nav :class="['fixed top-0 left-0 right-0 z-50 transition-all duration-300', isScrolled ? 'bg-white dark:bg-slate-900 shadow-md py-2' : 'bg-neutral-light py-4']">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center">
          <!-- Logo -->
          <div class="flex items-center cursor-pointer" @click="goLink(lang === 'zh-CN' ? '/' : '/en/')">
            <img src="/logo.svg" alt="行影集 Logo" class="w-8 h-8 mr-2">
            <div class="flex flex-col">
              <span class="text-xl font-bold text-neutral-dark dark:text-white leading-none">行影集</span>
              <span class="text-xs text-primary font-light">TrailSnap</span>
            </div>
          </div>

          <!-- Desktop Menu -->
          <div class="hidden md:flex items-center space-x-8">
            <button type="button" class="transition-colors" :class="navClass('home')" @click="scrollTo('home')">{{ t.nav.home }}</button>
            <button type="button" class="transition-colors" :class="navClass('core-features')" @click="scrollTo('core-features')">{{ t.nav.features }}</button>
            <button type="button" class="transition-colors text-neutral-dark dark:text-gray-300 hover:text-primary" @click="goLink(lang === 'zh-CN' ? '/docs/guide/install' : '/en/docs/guide/install')">{{ t.nav.quickStart }}</button>
          </div>

          <!-- Desktop Buttons -->
          <div class="hidden md:flex items-center space-x-4">
            <button class="px-6 py-2 rounded-lg bg-primary text-white hover:bg-primary-dark transform hover:scale-105 transition-all shadow-md hover:shadow-lg" @click="goLink(lang === 'zh-CN' ? '/docs/guide/install' : '/en/docs/guide/install')">{{ t.nav.download }}</button>
          </div>

          <!-- Mobile Hamburger -->
          <div class="md:hidden flex items-center">
            <button @click="toggleMobileMenu" class="text-neutral-dark dark:text-white focus:outline-none">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
          </div>
        </div>
      </div>

          <!-- Mobile Menu -->
          <div v-if="isMobileMenuOpen" class="md:hidden absolute top-full left-0 w-full bg-white dark:bg-slate-800 shadow-lg py-4 px-4 flex flex-col space-y-4">
        <button type="button" class="text-left w-fit transition-colors" :class="navClass('home')" @click="scrollTo('home')">{{ t.nav.home }}</button>
        <button type="button" class="text-left w-fit transition-colors" :class="navClass('core-features')" @click="scrollTo('core-features')">{{ t.nav.features }}</button>
        <button type="button" class="text-left w-fit transition-colors text-neutral-dark dark:text-gray-300 hover:text-primary" @click="goLink(lang === 'zh-CN' ? '/docs/guide/install' : '/en/docs/guide/install')">{{ t.nav.quickStart }}</button>
        <div class="flex space-x-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button class="flex-1 py-2 rounded-lg bg-primary text-white" @click="goLink(lang === 'zh-CN' ? '/docs/guide/install' : '/en/docs/guide/install')">{{ t.nav.download }}</button>
        </div>
      </div>
    </nav>

    <!-- 2. Hero Section -->
    <section id="home" class="relative pt-32 pb-20 lg:pt-40 lg:pb-32 bg-neutral-light dark:bg-slate-800/50 overflow-hidden">
      <!-- Background Gradients -->
      <div class="absolute top-0 left-0 w-1/3 h-full bg-gradient-to-r from-blue-50 dark:from-blue-900/20 to-transparent opacity-50"></div>
      <div class="absolute bottom-0 right-0 w-1/3 h-full bg-gradient-to-l from-blue-50 dark:from-blue-900/20 to-transparent opacity-50"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="flex flex-col lg:flex-row items-center">
          <!-- Text Content -->
          <div class="lg:w-[55%] text-center lg:text-left mb-12 lg:mb-0">
            <h1 class="text-3xl md:text-4xl lg:text-[42px] font-bold text-neutral-dark dark:text-white leading-tight mb-6">
              {{ t.hero.title1 }}<br>
              <span class="block mt-2">{{ t.hero.title2 }}</span>
            </h1>
            <p class="text-base md:text-lg text-neutral-gray dark:text-gray-400 mb-8 leading-relaxed max-w-2xl mx-auto lg:mx-0" v-html="t.hero.desc">
            </p>
            
            <!-- Tags -->
            <div class="flex flex-wrap justify-center lg:justify-start gap-3 mb-10">
              <span v-for="tag in t.hero.tags" :key="tag" class="px-4 py-2 bg-secondary dark:bg-secondary/20 rounded-full text-sm text-neutral-dark dark:text-gray-200 hover:-translate-y-1 transition-transform cursor-default">{{ tag }}</span>
            </div>

            <!-- Actions -->
            <div class="flex justify-center lg:justify-start gap-5">
              <button class="px-8 py-3 rounded-lg bg-primary text-white font-bold hover:bg-primary-dark hover:scale-105 transition-all shadow-lg hover:shadow-xl" @click="goLink(lang === 'zh-CN' ? '/docs/guide/install' : '/en/docs/guide/install')">{{ t.hero.download }}</button>
              <button class="px-8 py-3 rounded-lg border border-gray-300 dark:border-gray-600 text-neutral-dark dark:text-gray-200 hover:bg-white dark:hover:bg-slate-700 hover:border-gray-400 transition-all" @click="goLink(lang === 'zh-CN' ? '/docs/guide/user' : '/en/docs/guide/user')">{{ t.hero.details }}</button>
            </div>
          </div>

          <!-- Visual Content -->
          <div class="w-[60%] lg:w-[30%] relative flex justify-center">
            <div class="relative w-full max-w-md animate-float">
              <!-- Main Visual Placeholder (Phone App Interface) -->
              <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-float overflow-hidden border-8 border-white dark:border-slate-700 transform rotate-3 relative z-10 aspect-[9/16] flex items-center justify-center bg-gray-100 dark:bg-slate-900">
                <div class="text-center p-4">
                  <img src="/demo.jpg" alt="App 瀑布流界面演示" class="w-full h-full object-cover">
                </div>
              </div>
              
              <!-- Decorative Elements -->
              <div class="absolute -top-10 -right-10 text-6xl opacity-20 text-primary animate-pulse">📷</div>
              <div class="absolute bottom-10 -left-10 text-6xl opacity-20 text-primary">🗺️</div>
              
              <!-- Floating Card 1 -->
              <div class="absolute top-20 right-0 md:-right-12 bg-white dark:bg-slate-800 p-2 md:p-4 rounded-xl shadow-lg z-20 animate-float max-w-[180px] sm:max-w-none md:max-w-none" style="animation-delay: 1s;">
                <div class="flex items-center gap-3">
                  <div class="w-5 h-5 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center text-blue-500">🎫</div>
                  <div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ t.hero.card1.title }}</div>
                    <div class="text-sm font-bold dark:text-white">{{ t.hero.card1.desc }}</div>
                  </div>
                </div>
              </div>

              <!-- Floating Card 2 -->
              <div class="absolute bottom-32 left-0 md:-left-8 bg-white dark:bg-slate-800 p-2 md:p-4 rounded-xl shadow-lg z-20 animate-float max-w-[180px] md:max-w-none" style="animation-delay: 2s;">
                <div class="flex items-center gap-3">
                  <div class="w-5 h-5 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-500">📝</div>
                  <div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ t.hero.card2.title }}</div>
                    <div class="text-sm font-bold dark:text-white">{{ t.hero.card2.desc }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 2.5 Feature Screenshots -->
    <section class="py-20 bg-white dark:bg-slate-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-neutral-dark dark:text-white mb-4">{{ t.screenshots.title }}</h2>
          <div class="w-16 h-1 bg-primary mx-auto rounded-full"></div>
        </div>

        <div class="relative max-w-5xl mx-auto">
          <!-- Main Image Display -->
          <div class="relative aspect-video rounded-xl overflow-hidden shadow-2xl group bg-gray-100 dark:bg-slate-800">
             <div v-for="(shot, index) in featureScreenshots" :key="index" 
                 class="absolute inset-0 transition-opacity duration-500 ease-in-out"
                 :class="index === activeScreenshotIndex ? 'opacity-100 z-10' : 'opacity-0 z-0'">
              <img v-if="shot.image" :src="shot.image" :alt="shot.title" class="w-full h-full object-cover">
              <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-xl bg-gray-900">Image Placeholder: {{ shot.title }}</div>
              
              <!-- Caption Overlay -->
              <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-8 text-white">
                <h3 class="text-2xl font-bold mb-2">{{ shot.title }}</h3>
                <p class="text-lg opacity-90">{{ shot.desc }}</p>
              </div>
            </div>

            <!-- Arrows -->
            <button @click="prevScreenshot" class="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/30 hover:bg-black/50 rounded-full flex items-center justify-center text-white backdrop-blur-sm transition-all z-20 opacity-0 group-hover:opacity-100">←</button>
            <button @click="nextScreenshot" class="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/30 hover:bg-black/50 rounded-full flex items-center justify-center text-white backdrop-blur-sm transition-all z-20 opacity-0 group-hover:opacity-100">→</button>
          </div>

          <!-- Thumbnails/Indicators -->
          <div class="flex justify-center gap-3 mt-8">
            <button v-for="(shot, index) in featureScreenshots" :key="index"
                    @click="activeScreenshotIndex = index"
                    class="h-2 rounded-full transition-all duration-300"
                    :class="index === activeScreenshotIndex ? 'w-8 bg-primary' : 'w-2 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400'"></button>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Core Features -->
    <section id="core-features" class="py-20 bg-white dark:bg-slate-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-neutral-dark dark:text-white mb-4">{{ t.core.title }}</h2>
          <div class="w-16 h-1 bg-primary mx-auto rounded-full"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="(feature, index) in features" :key="index" 
               class="bg-white dark:bg-slate-800 rounded-xl p-8 shadow-soft hover:shadow-hover hover:-translate-y-2 transition-all duration-300 border border-transparent hover:border-blue-50 dark:hover:border-blue-900 group">
            <div class="text-5xl mb-6 group-hover:scale-110 transition-transform duration-300">{{ feature.icon }}</div>
            <h3 class="text-2xl font-bold text-neutral-dark dark:text-white mb-4 flex items-center gap-2">
              {{ feature.title }}
              <span v-if="feature.status" :class="['text-xs px-2 py-1 rounded-full font-normal', feature.statusColor]">{{ feature.status }}</span>
            </h3>
            <p class="text-neutral-gray dark:text-gray-400 leading-relaxed mb-6">{{ feature.desc }}</p>
            <div v-if="feature.tags" class="flex flex-wrap gap-2">
              <span v-for="tag in feature.tags" :key="tag" class="text-xs bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300 px-2 py-1 rounded">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. Features Overview -->
    <section class="py-20 bg-neutral-light dark:bg-slate-800/50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col lg:flex-row gap-12 lg:gap-20">
          <!-- Left List -->
          <div class="lg:w-[40%]">
            <h2 class="text-2xl md:text-[28px] font-bold text-neutral-dark dark:text-white mb-8 text-center lg:text-left">
              {{ t.overview.title }}
            </h2>
            <div class="space-y-4">
              <div v-for="(item, index) in overviewFeatures" :key="index" 
                   class="bg-white dark:bg-slate-800 rounded-lg p-4 border-l-4 border-primary cursor-pointer transition-all hover:shadow-md"
                   @click="activeFeatureIndex = index">
                <div class="flex justify-between items-center mb-2">
                  <div class="flex items-center gap-3">
                    <span class="text-xl text-primary">{{ item.icon }}</span>
                    <span class="text-lg font-medium text-neutral-dark dark:text-white">{{ item.title }}</span>
                  </div>
                  <span class="transform transition-transform dark:text-gray-400" :class="activeFeatureIndex === index ? 'rotate-180' : ''">⌄</span>
                </div>
                <ul v-show="activeFeatureIndex === index" class="ml-8 space-y-2 mt-2">
                  <li v-for="(subItem, subIndex) in item.items" :key="subIndex" class="text-sm text-neutral-gray dark:text-gray-400 flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full bg-primary"></div>
                    {{ subItem }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Right Visual -->
          <div class="lg:w-[60%] flex items-center justify-center">
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-float p-4 w-full max-w-xl aspect-[4/3] flex items-center justify-center border border-gray-100 dark:border-slate-700 relative overflow-hidden group">
              <div class="text-center">
                <div class="text-6xl mb-4">{{ overviewFeatures[activeFeatureIndex].icon }}</div>
                <h3 class="text-2xl font-bold text-neutral-dark dark:text-white">{{ overviewFeatures[activeFeatureIndex].title }}{{ t.overview.demoSuffix }}</h3>
                <p class="text-gray-400 mt-2">{{ t.overview.demoPlaceholder }}</p>
              </div>
              
              <!-- Hover Arrows (Mock) -->
              <div class="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/30 rounded-full flex items-center justify-center text-white cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity" @click="activeFeatureIndex = (activeFeatureIndex - 1 + overviewFeatures.length) % overviewFeatures.length">←</div>
              <div class="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 bg-black/30 rounded-full flex items-center justify-center text-white cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity" @click="activeFeatureIndex = (activeFeatureIndex + 1) % overviewFeatures.length">→</div>
              
              <!-- Dots -->
              <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                <div v-for="(_, i) in overviewFeatures" :key="i" 
                     class="w-2 h-2 rounded-full transition-colors"
                     :class="i === activeFeatureIndex ? 'bg-primary' : 'bg-gray-300 dark:bg-slate-600'"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 6. Testimonials -->
    <section class="py-20 bg-secondary/30 dark:bg-slate-800/30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-[28px] font-bold text-neutral-dark dark:text-white text-center mb-12">{{ t.testimonials.title }}</h2>
        
        <div class="max-w-3xl mx-auto bg-white dark:bg-slate-800 rounded-xl p-10 shadow-soft relative">
          <!-- Arrows -->
          <button @click="prevTestimonial" class="absolute left-[-20px] md:left-[-50px] top-1/2 -translate-y-1/2 w-10 h-10 bg-black/10 dark:bg-white/10 hover:bg-black/20 dark:hover:bg-white/20 rounded-full flex items-center justify-center text-neutral-dark dark:text-white transition-colors">←</button>
          <button @click="nextTestimonial" class="absolute right-[-20px] md:right-[-50px] top-1/2 -translate-y-1/2 w-10 h-10 bg-black/10 dark:bg-white/10 hover:bg-black/20 dark:hover:bg-white/20 rounded-full flex items-center justify-center text-neutral-dark dark:text-white transition-colors">→</button>

          <div class="text-center">
            <p class="text-lg md:text-xl text-neutral-gray dark:text-gray-300 italic leading-relaxed mb-8">
              "{{ testimonials[testimonialIndex].text }}"
            </p>
            <div class="flex items-center justify-center gap-4">
              <div class="w-12 h-12 bg-gray-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-xl">👤</div>
              <div class="text-left">
                <div class="font-bold text-neutral-dark dark:text-white">{{ testimonials[testimonialIndex].user }}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-700 px-2 py-0.5 rounded-full inline-block mt-1">{{ testimonials[testimonialIndex].role }}</div>
              </div>
            </div>
          </div>

          <!-- Dots -->
          <div class="flex justify-center gap-2 mt-8">
            <div v-for="(_, i) in testimonials" :key="i" 
                 class="w-2 h-2 rounded-full transition-colors cursor-pointer"
                 :class="i === testimonialIndex ? 'bg-primary' : 'bg-gray-300 dark:bg-slate-600'"
                 @click="testimonialIndex = i"></div>
          </div>
        </div>

        <!-- Trust Badges -->
        <div class="text-center mt-16">
          <h3 class="text-base font-bold text-neutral-dark dark:text-white mb-6">{{ t.trust.title }}</h3>
          <div class="flex justify-center gap-10 md:gap-20">
            <div class="flex flex-col items-center gap-2 group cursor-pointer" v-for="(item, index) in t.trust.items" :key="index">
              <div class="text-3xl text-primary group-hover:scale-110 transition-transform">{{ index === 0 ? '🔒' : (index === 1 ? '💾' : '🛡️') }}</div>
              <span class="text-sm text-neutral-gray dark:text-gray-400">{{ item }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 8. Footer -->
    <footer class="bg-neutral-dark dark:bg-[#1a1a1a] text-white pt-16 pb-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-12 text-center md:text-left">
          <!-- Col 1 -->
          <div>
            <h4 class="text-lg font-bold mb-6">{{ t.footer.about.title }}</h4>
            <p class="text-sm opacity-80 leading-relaxed">
              {{ t.footer.about.text }}
            </p>
          </div>
          <!-- Col 2 -->
          <div>
            <h4 class="text-lg font-bold mb-6">{{ t.footer.links.title }}</h4>
            <ul class="space-y-3 text-sm opacity-80">
              <li><a href="#" class="hover:text-primary transition-colors" @click.prevent="goLink(lang === 'zh-CN' ? '/' : '/en/')">{{ t.footer.links.items[0] }}</a></li>
              <li><a href="#" class="hover:text-primary transition-colors" @click.prevent="scrollTo('core-features')">{{ t.footer.links.items[1] }}</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">{{ t.footer.links.items[2] }}</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">{{ t.footer.links.items[3] }}</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">{{ t.footer.links.items[4] }}</a></li>
            </ul>
          </div>
          <!-- Col 3 -->
          <div>
            <h4 class="text-lg font-bold mb-6">{{ t.footer.contact.title }}</h4>
            <ul class="space-y-3 text-sm text-white/80">
              <li>{{ t.footer.contact.email }}：<a href="mailto:sixyuan044@gmail.com" class="hover:text-primary transition-colors">sixyuan044@gmail.com</a></li>
              <li>{{ t.footer.contact.wechat }}：忆墨痕</li>
              <li class="relative group">
                {{ t.footer.contact.qq }}：
                <span class="cursor-pointer border-b border-dashed border-white/40 hover:text-primary hover:border-primary transition-colors">
                  {{ t.footer.contact.scan }}
                </span>
                <!-- QQ Group QR Code Popup -->
                <div class="absolute bottom-full left-0 mb-2 w-64 bg-white p-2 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 text-neutral-dark">
                  <img src="/qq_group.jpg" alt="QQ群二维码" class="w-full h-auto rounded" />
                  <div class="text-xs text-center mt-1 text-black">扫码加入QQ群</div>
                  <!-- Arrow -->
                  <div class="absolute top-full left-4 border-8 border-transparent border-t-white"></div>
                </div>
              </li>
              <li>GitHub：<a href="https://github.com/LC044/TrailSnap" target="_blank" class="cursor-pointer border-b border-dashed border-white/40 hover:text-primary hover:border-primary transition-colors">LC044/TrailSnap</a></li>
            </ul>
          </div>
          <!-- Col 4 -->
          <div>
            <h4 class="text-lg font-bold mb-6">{{ t.footer.follow.title }}</h4>
            <div class="flex justify-center md:justify-start gap-4">
              <div v-for="link in socialLinks" :key="link.name" class="relative group cursor-pointer">
                <!-- Icon -->
                <div class="w-9 h-9 bg-white/10 rounded-full flex items-center justify-center hover:bg-white transition-colors overflow-hidden">
                   <img :src="link.icon" :alt="link.alt" class="w-full h-full object-cover p-1.5 opacity-80 group-hover:opacity-100" />
                </div>
                
                <!-- QR Code Popup -->
                <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-32 bg-white p-2 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50 text-neutral-dark">
                  <img :src="link.qrCode" :alt="link.alt + ' QR'" class="w-full h-auto rounded" />
                  <div class="text-xs text-center mt-1 text-black">{{ link.alt }}</div>
                  <!-- Arrow -->
                  <div class="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-white"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-white/10 pt-8 text-center">
          <p class="text-xs opacity-60">
            {{ t.footer.copyright }} <span class="mx-2">|</span> {{ t.footer.privacy }} <span class="mx-2">|</span> {{ t.footer.agreement }}
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useData } from 'vitepress'

const router = useRouter()
const { lang } = useData()

// Translations
const i18n = {
  'zh-CN': {
    nav: {
      home: '首页',
      features: '功能介绍',
      quickStart: '快速开始',
      download: '立即下载'
    },
    hero: {
      title1: 'AI赋能出行记忆',
      title2: '你的专属行影集',
      desc: '智能记录行程、整理旅行照片、生成专属记忆报告，<br class="hidden md:inline">让每一段出行都值得珍藏',
      tags: ['智能相册', '足迹相册', '生活相册'],
      download: '立即下载',
      details: '查看功能详情',
      card1: { title: '识别成功', desc: 'G1234 北京 -> 上海' },
      card2: { title: 'AI 日记生成', desc: '今天去滑雪（摔了一跤）...' }
    },
    screenshots: {
      title: '功能展示'
    },
    core: {
      title: '核心特色 · 重新定义相册记忆'
    },
    overview: {
      title: '功能概览 · 全方位覆盖出行记忆需求',
      demoSuffix: ' 演示',
      demoPlaceholder: '（此处展示功能演示动图/视频）'
    },
    testimonials: {
      title: '用户心声 · 用行影集珍藏每一段旅程'
    },
    trust: {
      title: '安全保障 · 数据真正属于你',
      items: ['全链路数据掌控', '本地存储', '隐私保护']
    },
    footer: {
      about: { title: '关于行影集', text: 'TrailSnap行影集是一款AI赋能的出行记忆珍藏工具，致力于让每一段出行都值得回味，让用户的数据真正属于自己。' },
      links: { title: '快速链接', items: ['首页', '功能介绍', '产品优势', '关于我们', '帮助中心'] },
      contact: { title: '联系我们', email: '邮箱', wechat: '微信公众号', qq: 'QQ群', scan: '扫码加入' },
      follow: { title: '关注我们' },
      copyright: '© 2025 TrailSnap行影集 版权所有',
      privacy: '隐私政策',
      agreement: '用户协议'
    }
  },
  'en-US': {
    nav: {
      home: 'Home',
      features: 'Features',
      quickStart: 'Quick Start',
      download: 'Download'
    },
    hero: {
      title1: 'AI-Empowered Travel Memories',
      title2: 'Your Exclusive TrailSnap',
      desc: 'Smartly record itineraries, organize travel photos, generate exclusive memory reports, <br class="hidden md:inline">making every trip worth cherishing.',
      tags: ['Smart Album', 'Footprint Album', 'Life Album'],
      download: 'Download',
      details: 'View Features',
      card1: { title: 'Success', desc: 'G1234 BJ -> SH' },
      card2: { title: 'AI Diary', desc: 'Skiing today (fell)...' }
    },
    screenshots: {
      title: 'Feature Screenshots'
    },
    core: {
      title: 'Core Features · Redefining Memories'
    },
    overview: {
      title: 'Feature Overview · Comprehensive Coverage',
      demoSuffix: ' Demo',
      demoPlaceholder: '(Feature demo GIF/Video here)'
    },
    testimonials: {
      title: 'User Voice · Cherish Every Journey'
    },
    trust: {
      title: 'Security · Your Data Truly Belongs to You',
      items: ['Full Data Control', 'Local Storage', 'Privacy Protection']
    },
    footer: {
      about: { title: 'About TrailSnap', text: 'TrailSnap is an AI-powered travel memory tool, dedicated to making every trip memorable and ensuring your data belongs to you.' },
      links: { title: 'Quick Links', items: ['Home', 'Features', 'Advantages', 'About Us', 'Help Center'] },
      contact: { title: 'Contact Us', email: 'Email', wechat: 'WeChat', qq: 'QQ Group', scan: 'Scan to Join' },
      follow: { title: 'Follow Us' },
      copyright: '© 2025 TrailSnap All Rights Reserved',
      privacy: 'Privacy Policy',
      agreement: 'User Agreement'
    }
  }
}

const t = computed(() => i18n[lang.value as keyof typeof i18n] || i18n['zh-CN'])

const featureScreenshotsList = {
  'zh-CN': [
    { title: '时光轴展示', desc: '丝滑的时间轴滚动效果', image: '/images/timeline.png' },
    { title: '地图模式', desc: '在地图上查看您的足迹，点亮每一个去过的城市', image: '/images/map.png' },
    { title: '智能分类', desc: '自动识别照片中的人物、景物，智能归类', image: '/images/classification.jpeg'}
  ],
  'en-US': [
    { title: 'Timeline View', desc: 'Smooth timeline scrolling effect', image: '' },
    { title: 'Map Mode', desc: 'View your footprints on the map and light up every city you visited', image: '' },
    { title: 'Smart Classification', desc: 'Automatically identify people and scenery in photos and classify them intelligently', image: '' }
  ]
}

const featureScreenshots = computed(() => featureScreenshotsList[lang.value as keyof typeof featureScreenshotsList] || featureScreenshotsList['zh-CN'])
const activeScreenshotIndex = ref(0)

const nextScreenshot = () => {
  activeScreenshotIndex.value = (activeScreenshotIndex.value + 1) % featureScreenshots.value.length
}

const prevScreenshot = () => {
  activeScreenshotIndex.value = (activeScreenshotIndex.value - 1 + featureScreenshots.value.length) % featureScreenshots.value.length
}

const featuresList = {
  'zh-CN': [
      {
    title: '智能相册',
    icon: '📸',
    desc: '人物识别、场景智能分类、智能搜索、足迹相册、照片OCR识别，轻松找到每一张旅行照片。',
    tags: ['人物识别', '智能分类', 'OCR识别']
  },
  {
    title: '行程记录',
    icon: '🎫',
    desc: '专属火车票、景区门票、演唱会门票管理功能，自动识别票据信息，识别国内5A级景区，清晰回顾每一段出行轨迹。',
    status: '开发中',
    tags: ['智能识别', '行程管理', '旅行足迹'],
    statusColor: 'bg-orange-100 text-orange-600'
  },
  {
    title: 'AI赋能',
    icon: '🤖',
    desc: '一句话生成旅行日记，自动剪辑15s旅行Vlog，智能修图筛选高质量照片，轻松打造专属旅行分享内容。',
    status: '待开发',
    statusColor: 'bg-blue-100 text-blue-600'
  }
  ],
  'en-US': [
    {
    title: 'Smart Album',
    icon: '📸',
    desc: 'Face recognition, smart scene classification, smart search, footprint album, photo OCR, easily find every travel photo.',
    tags: ['Face Recognition', 'Smart Classification', 'OCR']
  },
  {
    title: 'Itinerary Record',
    icon: '🎫',
    desc: 'Exclusive management for train tickets, scenic spot tickets, concert tickets, automatic ticket info recognition, 5A scenic spot recognition.',
    status: 'In Dev',
    tags: ['Smart Recognition', 'Itinerary Mgmt', 'Travel Footprint'],
    statusColor: 'bg-orange-100 text-orange-600'
  },
  {
    title: 'AI Empowerment',
    icon: '🤖',
    desc: 'One-sentence travel diary generation, auto-edit 15s travel Vlog, smart photo retouching and selection.',
    status: 'Planned',
    statusColor: 'bg-blue-100 text-blue-600'
  }
  ]
}

const features = computed(() => featuresList[lang.value as keyof typeof featuresList] || featuresList['zh-CN'])

const overviewFeaturesList = {
  'zh-CN': [
    { title: '智能相册', icon: '📸', items: ['精准人脸识别归类', '场景/物体智能标签', '自定义条件（智能）相册'] },
    { title: 'AI能力', icon: '🤖', items: ['一句话生成游记', 'Vlog智能剪辑', '照片智能精修'] },
    { title: '行程票据', icon: '🎫', items: ['票据自动识别录入', '国内5A景区位置识别', '多票据统一管理'] },
    { title: '数据可视化', icon: '📊', items: ['足迹地图点亮', '出行里程统计', '城市打卡记录'] },
    { title: '年度报告', icon: '📅', items: ['年度出行总结', '专属回忆生成', '分享朋友圈'] }
  ],
  'en-US': [
    { title: 'Smart Album', icon: '📸', items: ['Precise Face Clustering', 'Scene/Object Smart Tags', 'Custom Smart Albums'] },
    { title: 'AI Capabilities', icon: '🤖', items: ['One-sentence Diary', 'Smart Vlog Editing', 'Smart Photo Retouching'] },
    { title: 'Itinerary & Tickets', icon: '🎫', items: ['Auto Ticket Recognition', '5A Scenic Spot Location', 'Unified Ticket Mgmt'] },
    { title: 'Data Visualization', icon: '📊', items: ['Footprint Map Lighting', 'Travel Mileage Stats', 'City Check-in Records'] },
    { title: 'Annual Report', icon: '📅', items: ['Annual Travel Summary', 'Exclusive Memory Gen', 'Share to Moments'] }
  ]
}

const overviewFeatures = computed(() => overviewFeaturesList[lang.value as keyof typeof overviewFeaturesList] || overviewFeaturesList['zh-CN'])

const testimonialsList = {
  'zh-CN': [
    {
    text: '每次旅行拍的照片都乱七八糟，用了行影集后自动分类，还能识别车票生成行程，年底的年度报告更是惊喜，满满的回忆！',
    user: '旅行爱好者小A',
    role: '行影集内测用户'
  },
  {
    text: '最喜欢它的AI功能，自动剪辑的Vlog非常有感觉，省去了我大量剪辑视频的时间，强烈推荐给喜欢记录生活的朋友。',
    user: '摄影师大白',
    role: '资深用户'
  }
  ],
  'en-US': [
    {
    text: 'My travel photos used to be a mess. TrailSnap sorted them automatically and even generated itineraries from tickets. The annual report was a huge surprise!',
    user: 'Travel Enthusiast A',
    role: 'Beta User'
  },
  {
    text: 'I love the AI features the most. The auto-edited Vlog has great vibes and saved me tons of time. Highly recommended for life recorders.',
    user: 'Photographer Baymax',
    role: 'Power User'
  }
  ]
}

const testimonials = computed(() => testimonialsList[lang.value as keyof typeof testimonialsList] || testimonialsList['zh-CN'])

const isMobileMenuOpen = ref(false)
const isScrolled = ref(false)
const activeSection = ref<'home' | 'core-features'>('home')

// Carousel State
const activeFeatureIndex = ref(0)
const testimonialIndex = ref(0)

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
  const ids = ['home', 'core-features']
  const els = ids
    .map(id => document.getElementById(id))
    .filter((el): el is HTMLElement => Boolean(el))

  const io = new IntersectionObserver(
    entries => {
      const visible = entries
        .filter(e => e.isIntersecting)
        .sort((a, b) => (b.intersectionRatio ?? 0) - (a.intersectionRatio ?? 0))[0]
      if (!visible?.target?.id) return
      if (visible.target.id === 'home' || visible.target.id === 'core-features') {
        activeSection.value = visible.target.id
      }
    },
    { root: null, threshold: [0.15, 0.25, 0.4], rootMargin: '-20% 0px -60% 0px' }
  )

  els.forEach(el => io.observe(el))

  onUnmounted(() => {
    io.disconnect()
  })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const goLink = (path: string) => {
  router.go(path)
  isMobileMenuOpen.value = false
}

const scrollTo = (id: 'home' | 'core-features') => {
  const el = document.getElementById(id)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  isMobileMenuOpen.value = false
}

const navClass = (id: 'home' | 'core-features') => {
  const base = 'text-neutral-dark dark:text-gray-300 hover:text-primary'
  if (activeSection.value !== id) return base
  return 'text-primary font-medium border-b-2 border-primary'
}

const socialLinks = [
  {
    name: 'WeChat',
    icon: '/icons/wechat.svg',
    qrCode: '/qrcodes/wechat_qr.jpg',
    alt: '微信公众号'
  },
  {
    name: 'RedBook',
    icon: '/icons/xiaohongshu.svg',
    qrCode: '/qrcodes/xiaohongshu_qr.jpg',
    alt: '小红书'
  },
  {
    name: 'Bilibili',
    icon: '/icons/bilibili.svg',
    qrCode: '/qrcodes/bilibili_qr.jpg',
    alt: 'B站'
  }
]

const nextTestimonial = () => {
  testimonialIndex.value = (testimonialIndex.value + 1) % testimonials.value.length
}

const prevTestimonial = () => {
  testimonialIndex.value = (testimonialIndex.value - 1 + testimonials.value.length) % testimonials.value.length
}

</script>
<style scoped>
@keyframes float {
  0% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0); }
}

.animate-float {
  animation: float 4s ease-in-out infinite;
}
</style>
