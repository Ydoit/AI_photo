<template>
  <ReportPage class="section-location" :class="{ 'animate-in': isActive }">
    <div class="h-full flex flex-col p-2" ref="sectionRef">
      <!-- 标题区域 -->
      <div class="text-center mb-6 fade-in-up" :style="{ animationDelay: '0.1s' }">
        <h2 class="text-2xl font-bold text-orange-500 mb-2">步履所至 · 你的年度足迹地图</h2>
        <p class="text-sm text-slate-600 dark:text-slate-600 font-light">用镜头丈量山河，每一座城，都藏着你的独家时光</p>
      </div>

      <!-- 上半部分：地域数据汇总区 -->
      <div class="flex flex-col gap-4 mb-6">
        <div class="flex justify-between items-center gap-4">
          <!-- 省份卡片 -->
          <div class="flex-1 bg-[#FDFBF7] dark:bg-[#2A2A2A] rounded-2xl p-2 border border-slate-100 dark:border-slate-800 shadow-sm fade-in-left" :style="{ animationDelay: '0.2s' }">
             <div class="flex flex-col items-center justify-center h-full gap-1">
                <i class="mgc_earth_line text-2xl text-orange-500"></i>
                <div class="flex items-baseline gap-1">
                   <span class="text-3xl font-black text-orange-500 font-mono">{{ displayProvince }}</span>
                   <span class="text-xs text-slate-500">省</span>
                </div>
                <p class="text-xs text-slate-600 font-light text-center">山河万里，步履所至</p>
             </div>
          </div>

          <!-- 城市卡片 -->
          <div class="flex-1 bg-[#FDFBF7] dark:bg-[#2A2A2A] rounded-2xl p-2 border border-slate-100 dark:border-slate-800 shadow-sm fade-in-right" :style="{ animationDelay: '0.2s' }">
             <div class="flex flex-col items-center justify-center h-full gap-1">
                <i class="mgc_building_2_line text-2xl text-orange-500"></i>
                <div class="flex items-baseline gap-1">
                   <span class="text-3xl font-black text-orange-500 font-mono">{{ displayCity }}</span>
                   <span class="text-xs text-slate-500">城市</span>
                </div>
                <p class="text-xs text-slate-600 font-light text-center">一城一景，皆是回忆</p>
             </div>
          </div>
        </div>
        
        <!-- TOP1 城市补充 -->
        <div v-if="data.topCities && data.topCities.length > 0" class="text-center fade-in-up" :style="{ animationDelay: '0.5s' }">
           <p class="text-xs text-slate-600 font-light">
             ✨ 年度打卡最多：<span class="text-orange-500 font-bold">{{ data.topCities[0].cityName }}</span>（共{{ data.topCities[0].photoCount }}张照片）｜你的脚步，偏爱这座烟火小城
           </p>
        </div>
      </div>

      <!-- 下半部分：可视化地图核心区 -->
      <div class="flex-1 relative w-full h-full min-h-0 bg-white dark:bg-[#1E1E1E] rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden fade-in-up" :style="{ animationDelay: '0.6s' }">
         <div ref="mapContainer" class="w-full h-full absolute inset-0"></div>
         
         <!-- 地图加载中/失败 兜底 -->
         <div v-if="mapStatus !== 'loaded'" class="absolute inset-0 flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-900 z-10">
            <template v-if="mapStatus === 'loading'">
               <div class="animate-pulse flex flex-col items-center">
                  <i class="mgc_map_2_line text-4xl text-slate-300 mb-2"></i>
                  <span class="text-xs text-slate-600">足迹加载中，稍等片刻...</span>
               </div>
            </template>
            <template v-else-if="mapStatus === 'error'">
               <div class="flex flex-col items-center" @click="initMap">
                  <i class="mgc_ghost_line text-4xl text-slate-300 mb-2"></i>
                  <span class="text-xs text-slate-600">地图走丢了，点击重试</span>
               </div>
            </template>
            <template v-else-if="mapStatus === 'empty'">
               <div class="flex flex-col items-center">
                  <i class="mgc_footprint_line text-4xl text-slate-300 mb-2"></i>
                  <span class="text-xs text-slate-600">暂未留下足迹印记</span>
                  <span class="text-[10px] text-slate-300 mt-1">下一年，愿你奔赴山海</span>
               </div>
            </template>
         </div>
      </div>
    </div>
  </ReportPage>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import ReportPage from './ReportPage.vue';
import type { LocationMetrics } from '@/types/annualReport';
import * as echarts from 'echarts';
import { useIntersectionObserver } from '@vueuse/core';
import 'mingcute_icon/font/mingcute.css'; // Ensure icons are available if not globally imported

const props = defineProps<{
  data: LocationMetrics;
}>();

const isActive = ref(false);
const sectionRef = ref<HTMLElement | null>(null);

useIntersectionObserver(
  sectionRef,
  ([{ isIntersecting }]) => {
    if (isIntersecting && !isActive.value) {
      isActive.value = true;
    }
  },
  { threshold: 0.5 }
);

const displayProvince = ref(0);
const displayCity = ref(0);
const mapContainer = ref<HTMLElement | null>(null);
const mapStatus = ref<'loading' | 'loaded' | 'error' | 'empty'>('loading');
let myMap: echarts.ECharts | null = null;

// 数字滚动动画
const animateValue = (start: number, end: number, duration: number, callback: (val: number) => void) => {
  const startTime = performance.now();
  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // EaseOutExpo
    const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
    
    const value = Math.floor(start + (end - start) * easeProgress);
    callback(value);

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };
  requestAnimationFrame(animate);
};

// 监听 isActive 触发动画
watch(isActive, (newVal) => {
  if (newVal) {
    // 重置并开始计数动画
    displayProvince.value = 0;
    displayCity.value = 0;
    setTimeout(() => {
       animateValue(0, props.data.lightenProvinceNum, 1200, (val) => displayProvince.value = val);
       animateValue(0, props.data.lightenCityNum, 1200, (val) => displayCity.value = val);
    }, 100);
    
    // 如果地图未加载，尝试加载
    if (!myMap) {
        initMap();
    } else {
        myMap.resize();
    }
  }
});

const initMap = async () => {
  if (!mapContainer.value) return;
  
  if (props.data.locationPoints.length === 0) {
      mapStatus.value = 'empty';
      return;
  }

  mapStatus.value = 'loading';
  
  try {
      // 获取地图数据
      const response = await fetch('/api/medias/geojson?level=province');
      if (!response.ok) throw new Error('Map fetch failed');
      const chinaJson = await response.json();
      
      echarts.registerMap('china', chinaJson);
      
      myMap = echarts.init(mapContainer.value);
      
      renderMap();
      mapStatus.value = 'loaded';
      
      // 监听窗口大小变化
      window.addEventListener('resize', handleResize);
  } catch (e) {
      console.error(e);
      mapStatus.value = 'error';
  }
};

const renderMap = () => {
    if (!myMap) return;
    
    // 准备数据
    // 1. 点亮省份：根据 topCities 中的 provinceName 或者 locationPoints 推断
    // 由于后端没直接给 visitedProvinces 列表，我们可以从 topCities 或 points 中提取
    // 这里简单处理：假设所有有点的省份都点亮。
    // 为了更准确，最好后端给 visitedProvinces，但接口定义只有 lightenProvinceNum。
    // 我们用 locationPoints 里的数据无法直接映射到省份名（除非有逆地理编码）。
    // 暂时用 topCities 中的 provinceName 作为已访问省份的高亮依据（如果不全也没办法，Mock数据里有几个）。
    // 更好的方式：Mock数据里 locationPoints 应该包含 provinceName，或者我们假设 China Map 的 feature name 匹配 provinceName。
    // 在 Mock 数据中，points 有 'name' (城市名)。
    // 实际上 ECharts 'china' map 的 regions 是省份。
    // 我们需要把城市点映射到省份。
    // 既然没有直接的省份列表，我们可以构造一个简单的 mapData，所有省份默认颜色，特定省份高亮。
    // 但因为不知道所有点对应的省份，我们主要展示 Points 和 Top Cities 所在省份。
    
    const visitedProvinces = new Set(props.data.topCities.map(c => c.provinceName));
    // 补充：从 locationPoints 猜测省份？太复杂且不准。
    // 简化：只高亮 topCities 里的省份，或者如果 Mock 数据不够全，就只高亮几个示例。
    // 用户要求："Light up areas: User visited provinces/cities".
    // 让我们假设 API 能返回所有 visited provinces。当前接口没给 list。
    // 为了效果，我手动添加一些 Mock 省份到 visitedProvinces 集合中（仅用于演示效果），或者仅使用 topCities。
    // 鉴于这是前端任务，我会尽量利用现有数据。
    
    const mapData = Array.from(visitedProvinces).map(p => ({
        name: p,
        itemStyle: {
            areaColor: {
                type: 'linear',
                x: 0, y: 0, x2: 1, y2: 1,
                colorStops: [{ offset: 0, color: '#FEE2D0' }, { offset: 1, color: '#F97316' }] // 浅橙 -> 深橙
            },
            borderColor: '#F59E0B', // 暖金
            borderWidth: 1
        }
    }));

    const scatterData = props.data.locationPoints.map(p => ({
        name: p.name,
        value: [p.lng, p.lat, p.count],
        itemStyle: {
            color: p.name === props.data.topCities[0]?.cityName ? '#F97316' : '#FDBA74'
        }
    }));
    
    const topCity = props.data.topCities[0];
    
    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderColor: '#F97316',
            textStyle: { color: '#333' },
            formatter: (params: any) => {
                if (params.seriesType === 'scatter' || params.seriesType === 'effectScatter') {
                    return `
                        <div class="p-1">
                           <div class="font-bold text-orange-500 mb-1">${params.name}</div>
                           <div class="text-xs text-slate-500">共拍摄 ${params.value[2]} 张照片</div>
                           <div class="text-xs text-slate-600 mt-1">这一程的风景，都被你好好收藏</div>
                        </div>
                    `;
                }
                return params.name;
            }
        },
        geo: {
            map: 'china',
            roam: true, // 允许缩放
            zoom: 1.2,
            center: topCity ? [props.data.locationPoints.find(p=>p.name===topCity.cityName)?.lng || 104.1, props.data.locationPoints.find(p=>p.name===topCity.cityName)?.lat || 37.5] : [104.1, 37.5], // Focus on Top 1 or Center
            label: { emphasis: { show: false } },
            itemStyle: {
                normal: {
                    areaColor: '#f1f5f9', // 浅灰
                    borderColor: '#cbd5e1',
                    borderWidth: 1
                },
                emphasis: {
                    areaColor: '#e2e8f0'
                }
            },
            regions: mapData
        },
        series: [
            {
                name: '足迹点',
                type: 'scatter',
                coordinateSystem: 'geo',
                data: scatterData,
                symbolSize: (val: any) => Math.min(Math.max(val[2] / 5, 6), 20), // 根据照片数调整大小
                label: {
                    formatter: '{b}',
                    position: 'right',
                    show: false
                },
                itemStyle: {
                    color: '#F97316',
                    shadowBlur: 10,
                    shadowColor: 'rgba(249, 115, 22, 0.5)'
                }
            },
            {
                name: 'Top1焦点',
                type: 'effectScatter',
                coordinateSystem: 'geo',
                data: topCity ? scatterData.filter(p => p.name === topCity.cityName) : [],
                symbolSize: 20,
                showEffectOn: 'render',
                rippleEffect: {
                    brushType: 'stroke',
                    scale: 3
                },
                itemStyle: {
                    color: '#F97316',
                    shadowBlur: 10,
                    shadowColor: '#333'
                },
                zlevel: 1
            }
        ]
    };
    
    myMap.setOption(option);
};

const handleResize = () => {
    myMap?.resize();
};

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    myMap?.dispose();
});

</script>

<style scoped>
.animate-in .fade-in-up {
  animation: fadeInUp 0.8s ease-out forwards;
  opacity: 0;
}

.animate-in .fade-in-left {
  animation: fadeInLeft 0.8s ease-out forwards;
  opacity: 0;
}

.animate-in .fade-in-right {
  animation: fadeInRight 0.8s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
