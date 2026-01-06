<template>
  <div class="min-h-screen bg-white dark:bg-slate-900 text-neutral-dark dark:text-gray-100 font-sans overflow-x-hidden">
    
    <!-- 1. Navbar -->
    <nav :class="['fixed top-0 left-0 right-0 z-50 transition-all duration-300', isScrolled ? 'bg-white dark:bg-slate-900 shadow-md py-2' : 'bg-neutral-light py-4']">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center">
          <!-- Logo -->
          <div class="flex items-center cursor-pointer" @click="goLink('/')">
            <img src="/logo.svg" alt="行影集 Logo" class="w-8 h-8 mr-2">
            <div class="flex flex-col">
              <span class="text-xl font-bold text-neutral-dark dark:text-white leading-none">行影集</span>
              <span class="text-xs text-primary font-light">TrailSnap</span>
            </div>
          </div>

          <!-- Desktop Menu -->
          <div class="hidden md:flex items-center space-x-8">
            <a href="#" class="text-primary font-medium border-b-2 border-primary">首页</a>
            <a href="/docs/guide/user" class="text-neutral-dark dark:text-gray-300 hover:text-primary transition-colors">功能介绍</a>
            <a href="/docs/guide/install" class="text-neutral-dark dark:text-gray-300 hover:text-primary transition-colors">快速开始</a>
          </div>

          <!-- Desktop Buttons -->
          <div class="hidden md:flex items-center space-x-4">
            <button class="px-6 py-2 rounded-lg bg-primary text-white hover:bg-primary-dark transform hover:scale-105 transition-all shadow-md hover:shadow-lg" @click="goLink('/docs/guide/install')">立即下载</button>
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
        <a href="#" class="text-primary font-medium border-b-2 border-primary w-fit">首页</a>
        <a href="/docs/guide/user" class="text-neutral-dark dark:text-gray-300">功能介绍</a>
        <a href="#" class="text-neutral-dark dark:text-gray-300">产品优势</a>
        <a href="#" class="text-neutral-dark dark:text-gray-300">关于我们</a>
        <div class="flex space-x-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <button class="flex-1 py-2 rounded-lg bg-primary text-white" @click="goLink('/docs/guide/install')">立即下载</button>
        </div>
      </div>
    </nav>

    <!-- 2. Hero Section -->
    <section class="relative pt-32 pb-20 lg:pt-40 lg:pb-32 bg-neutral-light dark:bg-slate-800/50 overflow-hidden">
      <!-- Background Gradients -->
      <div class="absolute top-0 left-0 w-1/3 h-full bg-gradient-to-r from-blue-50 dark:from-blue-900/20 to-transparent opacity-50"></div>
      <div class="absolute bottom-0 right-0 w-1/3 h-full bg-gradient-to-l from-blue-50 dark:from-blue-900/20 to-transparent opacity-50"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="flex flex-col lg:flex-row items-center">
          <!-- Text Content -->
          <div class="lg:w-[55%] text-center lg:text-left mb-12 lg:mb-0">
            <h1 class="text-3xl md:text-4xl lg:text-[42px] font-bold text-neutral-dark dark:text-white leading-tight mb-6">
              AI赋能出行记忆<br>
              <span class="block mt-2">你的专属行影集</span>
            </h1>
            <p class="text-base md:text-lg text-neutral-gray dark:text-gray-400 mb-8 leading-relaxed max-w-2xl mx-auto lg:mx-0">
              智能记录行程、整理旅行照片、生成专属记忆报告，<br class="hidden md:inline">让每一段出行都值得珍藏
            </p>
            
            <!-- Tags -->
            <div class="flex flex-wrap justify-center lg:justify-start gap-3 mb-10">
              <span class="px-4 py-2 bg-secondary dark:bg-secondary/20 rounded-full text-sm text-neutral-dark dark:text-gray-200 hover:-translate-y-1 transition-transform cursor-default">智能相册</span>
              <span class="px-4 py-2 bg-secondary dark:bg-secondary/20 rounded-full text-sm text-neutral-dark dark:text-gray-200 hover:-translate-y-1 transition-transform cursor-default">AI识别车票</span>
              <span class="px-4 py-2 bg-secondary dark:bg-secondary/20 rounded-full text-sm text-neutral-dark dark:text-gray-200 hover:-translate-y-1 transition-transform cursor-default">数据可视化</span>
            </div>

            <!-- Actions -->
            <div class="flex justify-center lg:justify-start gap-5">
              <button class="px-8 py-3 rounded-lg bg-primary text-white font-bold hover:bg-primary-dark hover:scale-105 transition-all shadow-lg hover:shadow-xl" @click="goLink('/docs/guide/install')">立即下载</button>
              <button class="px-8 py-3 rounded-lg border border-gray-300 dark:border-gray-600 text-neutral-dark dark:text-gray-200 hover:bg-white dark:hover:bg-slate-700 hover:border-gray-400 transition-all" @click="goLink('/docs/guide/user')">查看功能详情</button>
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
                    <div class="text-xs text-gray-500 dark:text-gray-400">识别成功</div>
                    <div class="text-sm font-bold dark:text-white">G1234 北京 -> 上海</div>
                  </div>
                </div>
              </div>

              <!-- Floating Card 2 -->
              <div class="absolute bottom-32 left-0 md:-left-8 bg-white dark:bg-slate-800 p-2 md:p-4 rounded-xl shadow-lg z-20 animate-float max-w-[180px] md:max-w-none" style="animation-delay: 2s;">
                <div class="flex items-center gap-3">
                  <div class="w-5 h-5 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-500">📝</div>
                  <div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">AI 日记生成</div>
                    <div class="text-sm font-bold dark:text-white">今天去滑雪（摔了一跤）...</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Core Features -->
    <section class="py-20 bg-white dark:bg-slate-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold text-neutral-dark dark:text-white mb-4">核心特色 · 重新定义相册记忆</h2>
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
              功能概览 · 全方位覆盖出行记忆需求
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
                <h3 class="text-2xl font-bold text-neutral-dark dark:text-white">{{ overviewFeatures[activeFeatureIndex].title }} 演示</h3>
                <p class="text-gray-400 mt-2">（此处展示功能演示动图/视频）</p>
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

    <!-- 5. Data Visualization -->
    <section class="py-20 bg-white dark:bg-slate-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-[28px] font-bold text-neutral-dark dark:text-white mb-4">数据可视化 · 让出行记忆更直观</h2>
          <div class="w-16 h-1 bg-primary mx-auto rounded-full"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <!-- Card 1 -->
          <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-2 transition-all duration-300 text-center border border-gray-50 dark:border-slate-700">
            <div class="text-4xl text-primary mb-4 mx-auto">📊</div>
            <h3 class="text-xl font-medium text-neutral-dark dark:text-white mb-3">出行统计图表</h3>
            <p class="text-sm text-neutral-gray dark:text-gray-400 leading-relaxed">直观展示年度出行次数、城市分布、里程统计，清晰了解你的出行轨迹。</p>
          </div>
          <!-- Card 2 -->
          <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-2 transition-all duration-300 text-center border border-gray-50 dark:border-slate-700">
            <div class="text-4xl text-primary mb-4 mx-auto">⏳</div>
            <h3 class="text-xl font-medium text-neutral-dark dark:text-white mb-3">行程时间轴</h3>
            <p class="text-sm text-neutral-gray dark:text-gray-400 leading-relaxed">按时间顺序串联所有出行行程，搭配照片与票据，一键回顾完整旅行过程。</p>
          </div>
          <!-- Card 3 -->
          <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-2 transition-all duration-300 text-center border border-gray-50 dark:border-slate-700">
            <div class="text-4xl text-primary mb-4 mx-auto">🛣️</div>
            <h3 class="text-xl font-medium text-neutral-dark dark:text-white mb-3">线路里程</h3>
            <p class="text-sm text-neutral-gray dark:text-gray-400 leading-relaxed">自动计算各次出行的线路里程，生成总里程统计，见证你的每一段旅程。</p>
          </div>
          <!-- Card 4 -->
          <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-2 transition-all duration-300 text-center border border-gray-50 dark:border-slate-700">
            <div class="text-4xl text-primary mb-4 mx-auto">📅</div>
            <h3 class="text-xl font-medium text-neutral-dark dark:text-white mb-3">年度出行报告</h3>
            <p class="text-sm text-neutral-gray dark:text-gray-400 leading-relaxed">自动生成年度出行统计报告，包含照片墙、出行城市、景点、时间轴等核心内容。</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 6. Testimonials -->
    <section class="py-20 bg-secondary/30 dark:bg-slate-800/30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-[28px] font-bold text-neutral-dark dark:text-white text-center mb-12">用户心声 · 用行影集珍藏每一段旅程</h2>
        
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
          <h3 class="text-base font-bold text-neutral-dark dark:text-white mb-6">安全保障 · 数据真正属于你</h3>
          <div class="flex justify-center gap-10 md:gap-20">
            <div class="flex flex-col items-center gap-2 group cursor-pointer">
              <div class="text-3xl text-primary group-hover:scale-110 transition-transform">🔒</div>
              <span class="text-sm text-neutral-gray dark:text-gray-400">全链路数据掌控</span>
            </div>
            <div class="flex flex-col items-center gap-2 group cursor-pointer">
              <div class="text-3xl text-primary group-hover:scale-110 transition-transform">💾</div>
              <span class="text-sm text-neutral-gray dark:text-gray-400">本地存储</span>
            </div>
            <div class="flex flex-col items-center gap-2 group cursor-pointer">
              <div class="text-3xl text-primary group-hover:scale-110 transition-transform">🛡️</div>
              <span class="text-sm text-neutral-gray dark:text-gray-400">隐私保护</span>
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
            <h4 class="text-lg font-bold mb-6">关于行影集</h4>
            <p class="text-sm opacity-80 leading-relaxed">
              TrailSnap行影集是一款AI赋能的出行记忆珍藏工具，致力于让每一段出行都值得回味，让用户的数据真正属于自己。
            </p>
          </div>
          <!-- Col 2 -->
          <div>
            <h4 class="text-lg font-bold mb-6">快速链接</h4>
            <ul class="space-y-3 text-sm opacity-80">
              <li><a href="#" class="hover:text-primary transition-colors">首页</a></li>
              <li><a href="/docs/guide/user" class="hover:text-primary transition-colors">功能介绍</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">产品优势</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">关于我们</a></li>
              <li><a href="#" class="hover:text-primary transition-colors">帮助中心</a></li>
            </ul>
          </div>
          <!-- Col 3 -->
          <div>
            <h4 class="text-lg font-bold mb-6">联系我们</h4>
            <ul class="space-y-3 text-sm text-white/80">
              <li>邮箱：<a href="mailto:sixyuan044@gmail.com" class="hover:text-primary transition-colors">sixyuan044@gmail.com</a></li>
              <li>微信公众号：忆墨痕</li>
              <li class="relative group">
                QQ群：
                <span class="cursor-pointer border-b border-dashed border-white/40 hover:text-primary hover:border-primary transition-colors">
                  扫码加入
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
            <h4 class="text-lg font-bold mb-6">关注我们</h4>
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
            © 2025 TrailSnap行影集 版权所有 <span class="mx-2">|</span> 隐私政策 <span class="mx-2">|</span> 用户协议
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vitepress'

const router = useRouter()
const isMobileMenuOpen = ref(false)
const isScrolled = ref(false)

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
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

const goLink = (path: string) => {
  router.go(path)
  isMobileMenuOpen.value = false
}

// Mock Data
const features = [
  {
    title: '智能相册',
    icon: '📸',
    desc: '精准人物识别、场景智能分类、照片OCR识别，轻松找到每一张旅行照片。瀑布流展示设计，浏览体验更流畅。',
    tags: ['人物识别', '智能分类', 'OCR识别']
  },
  {
    title: '行程记录',
    icon: '🎫',
    desc: '专属火车票、景区门票、演唱会门票管理功能，自动识别票据信息，生成完整行程 timeline，清晰回顾每一段出行轨迹。',
    status: '开发中',
    statusColor: 'bg-orange-100 text-orange-600'
  },
  {
    title: 'AI赋能',
    icon: '🤖',
    desc: '一句话生成旅行日记，自动剪辑15s旅行Vlog，智能修图筛选高质量照片，轻松打造专属旅行分享内容。',
    status: '待开发',
    statusColor: 'bg-blue-100 text-blue-600'
  }
]

const overviewFeatures = [
  { title: '智能相册', icon: '📸', items: ['精准人脸识别归类', '场景/物体智能标签', '自定义条件（智能）相册'] },
  { title: 'AI能力', icon: '🤖', items: ['一句话生成游记', 'Vlog智能剪辑', '照片智能精修'] },
  { title: '行程票据', icon: '🎫', items: ['票据自动识别录入', '行程时间轴生成', '多票据统一管理'] },
  { title: '数据可视化', icon: '📊', items: ['足迹地图点亮', '出行里程统计', '城市打卡记录'] },
  { title: '年度报告', icon: '📅', items: ['年度出行总结', '专属回忆生成', '分享朋友圈'] }
]

const testimonials = [
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
]

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
  testimonialIndex.value = (testimonialIndex.value + 1) % testimonials.length
}

const prevTestimonial = () => {
  testimonialIndex.value = (testimonialIndex.value - 1 + testimonials.length) % testimonials.length
}

</script>
<style scoped>
@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

.animate-float {
  animation: float 4s ease-in-out infinite;
}
</style>
