<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300 p-4 pb-10">
    
    <div class="max-w-[1400px] mx-auto mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button 
          @click="$emit('back')" 
          class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
        >
          <ArrowLeft class="w-4 h-4" />
          <span>返回列表</span>
        </button>
        <h1 class="text-2xl font-light text-slate-800 dark:text-white tracking-wide">
          旅行足迹报告
        </h1>
      </div>
      
      <div class="flex bg-white dark:bg-slate-800 rounded-lg p-1 border border-slate-200 dark:border-slate-700">
        <span class="px-3 py-1 text-xs font-medium text-slate-500 dark:text-slate-400 self-center">2024</span>
      </div>
    </div>

    <div class="max-w-[1400px] mx-auto space-y-6">
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 group">
          <div class="absolute right-0 top-0 w-32 h-32 bg-primary-50 dark:bg-slate-700 rounded-full blur-3xl -mr-10 -mt-10 transition-colors"></div>
          <div class="relative z-10">
            <div class="flex items-center gap-2 mb-2">
              <div class="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                <Route class="w-5 h-5" />
              </div>
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">年度总里程</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-4xl font-bold text-slate-800 dark:text-white font-mono">{{ totalStats.distance.toLocaleString() }}</span>
              <span class="text-sm text-slate-500">km</span>
            </div>
            <div class="mt-2 text-xs text-slate-400">
              超过了 <span class="text-blue-600 dark:text-blue-400 font-bold">92%</span> 的旅行者
            </div>
          </div>
        </div>

        <div class="relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div class="relative z-10">
            <div class="flex items-center gap-2 mb-2">
              <div class="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400">
                <MapPin class="w-5 h-5" />
              </div>
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">点亮城市</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-4xl font-bold text-slate-800 dark:text-white font-mono">{{ totalStats.cities }}</span>
              <span class="text-sm text-slate-500">个</span>
            </div>
             <div class="mt-2 text-xs text-slate-400">
              最北到达 <span class="text-emerald-600 dark:text-emerald-400 font-bold">哈尔滨</span>
            </div>
          </div>
        </div>

        <div class="relative overflow-hidden bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <div class="relative z-10">
            <div class="flex items-center gap-2 mb-2">
              <div class="p-2 rounded-lg bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
                <Clock class="w-5 h-5" />
              </div>
              <span class="text-sm text-slate-500 dark:text-slate-400 font-medium">在路上</span>
            </div>
            <div class="flex items-baseline gap-2">
              <span class="text-4xl font-bold text-slate-800 dark:text-white font-mono">{{ totalStats.hours }}</span>
              <span class="text-sm text-slate-500">小时</span>
            </div>
             <div class="mt-2 text-xs text-slate-400">
              约等于连续乘坐 <span class="text-purple-600 dark:text-purple-400 font-bold">2.5</span> 天
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-2xl p-1 shadow-md border border-slate-200 dark:border-slate-700 relative h-[600px] overflow-hidden">
        <div class="absolute top-4 right-4 z-20 bg-white/80 dark:bg-slate-700/80 backdrop-blur p-2 rounded-lg shadow border border-slate-200 dark:border-slate-600">
           <span class="text-xs font-bold text-slate-500 dark:text-slate-300">GEO TRAIL</span>
         </div>
         
         <div ref="mapContainer" class="w-full h-full rounded-xl"></div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 h-80 flex flex-col">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4">出行频率趋势</h3>
          <div ref="trendChart" class="flex-1 w-full"></div>
        </div>
        
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 h-80 flex flex-col">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4">最爱去的城市</h3>
          <div ref="barChart" class="flex-1 w-full"></div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, computed } from 'vue';
import * as echarts from 'echarts';
import { ArrowLeft, Route, MapPin, Clock } from 'lucide-vue-next';
import { injectTheme } from '@/composables/useTheme';

// 接收父组件传入的主题和模式
const props = defineProps({
  isDarkMode: Boolean,
  themeColor: String, // '#1E88E5' etc
  tickets: {
    type: Array,
    default: () => []
  }
});

// 2. 注入全局状态
const { isDarkMode, currentTheme } = injectTheme();

// 3. 提取所需的响应式值
const isDark = isDarkMode;
const themeColor = computed(() => currentTheme.value.primary);
defineEmits(['back']);

// --- DOM Refs ---
const mapContainer = ref(null);
const trendChart = ref(null);
const barChart = ref(null);
let myMap = null;
let myTrend = null;
let myBar = null;

// --- 模拟数据 (Demo用，实际应由 props.tickets 计算) ---
const totalStats = ref({
  distance: 12580,
  cities: 14,
  hours: 68
});

// --- 城市经纬度字典 (核心：ECharts 需要经纬度) ---
// 实际项目中建议后端返回或引入完整的城市坐标库
const cityCoords = {
  '北京南': [116.407526, 39.90403], '北京': [116.407526, 39.90403],
  '上海虹桥': [121.473701, 31.230416], '上海': [121.473701, 31.230416],
  '广州南': [113.264434, 23.129162], '广州': [113.264434, 23.129162],
  '深圳北': [114.057868, 22.543099], '深圳': [114.057868, 22.543099],
  '成都东': [104.066541, 30.572269], '成都': [104.066541, 30.572269],
  '重庆北': [106.551556, 29.563009], '重庆': [106.551556, 29.563009],
  '杭州东': [120.15507, 30.274085], '杭州': [120.15507, 30.274085],
  '西安北': [108.93977, 34.341574], '西安': [108.93977, 34.341574],
  '武汉': [114.305393, 30.593099],
  '长沙南': [112.938814, 28.228209],
  '南京南': [118.796877, 32.060255],
  '哈尔滨': [126.534967, 45.803775],
  '兰州西': [103.834303, 36.061089],
  '拉萨': [91.140856, 29.645554],
  '乌鲁木齐': [87.616848, 43.825592]
};

// --- ECharts 初始化逻辑 ---

// 1. 准备地图数据 (Lines 和 Points)
const getMapData = () => {
  // 模拟一些线路数据，实际应遍历 props.tickets
  const routes = [
    { from: '北京南', to: '上海虹桥' },
    { from: '上海虹桥', to: '成都东' },
    { from: '成都东', to: '重庆北' },
    { from: '广州南', to: '长沙南' },
    { from: '长沙南', to: '武汉' },
    { from: '武汉', to: '北京南' },
    { from: '西安北', to: '兰州西' },
    { from: '兰州西', to: '乌鲁木齐' } // 长距离展示曲线效果好
  ];

  const linesData = [];
  const pointsData = new Set();

  routes.forEach(route => {
    const fromCoord = cityCoords[route.from];
    const toCoord = cityCoords[route.to];
    
    if (fromCoord && toCoord) {
      linesData.push({
        coords: [fromCoord, toCoord]
      });
      pointsData.add(JSON.stringify({ name: route.from, value: [...fromCoord, 10] })); // value[2] can be weight
      pointsData.add(JSON.stringify({ name: route.to, value: [...toCoord, 10] }));
    }
  });

  return {
    lines: linesData,
    points: Array.from(pointsData).map(JSON.parse)
  };
};

// 2. 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return;
  
  myMap = echarts.init(mapContainer.value);

  // 加载中国地图 GeoJSON (使用阿里云的 CDN 数据源作为示例)
  try {
    const response = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json');
    const chinaJson = await response.json();
    echarts.registerMap('china', chinaJson);

    renderMap();
  } catch (e) {
    console.error("Map load failed", e);
    // 可以在这里显示一个错误提示或者降级方案
  }
};

const renderMap = () => {
  if (!myMap) return;

  const { lines, points } = getMapData();
  const isDark = props.isDarkMode;
  const mainColor = themeColor.value || '#1E88E5';

  const option = {
    backgroundColor: 'transparent',
    geo: {
      map: 'china',
      roam: true, // 允许缩放平移
      zoom: 1.2,
      label: { emphasis: { show: false } },
      itemStyle: {
        normal: {
          areaColor: isDark ? '#1e293b' : '#eff6ff', // Slate-800 : Blue-50
          borderColor: isDark ? '#334155' : '#bfdbfe', // Slate-700 : Blue-200
          borderWidth: 1
        },
        emphasis: {
          areaColor: isDark ? '#334155' : '#dbeafe'
        }
      }
    },
    series: [
      // 1. 轨迹线 (带特效)
      {
        type: 'lines',
        zlevel: 1,
        effect: {
          show: true,
          period: 6,
          trailLength: 0.7,
          color: mainColor, // 飞机轨迹颜色
          symbolSize: 3
        },
        lineStyle: {
          normal: {
            color: mainColor,
            width: 0,
            curveness: 0.2 // 曲线程度
          }
        },
        data: lines
      },
      // 2. 轨迹线 (底线)
      {
        type: 'lines',
        zlevel: 2,
        symbol: ['none', 'arrow'],
        symbolSize: 10,
        effect: {
          show: true,
          period: 6,
          trailLength: 0,
          symbol: 'plane', // 飞机图标
          symbolSize: 15
        },
        lineStyle: {
          normal: {
            color: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)', // 淡淡的连线
            width: 1,
            opacity: 0.4,
            curveness: 0.2
          }
        },
        data: lines
      },
      // 3. 城市散点 (带有涟漪特效)
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        zlevel: 3,
        rippleEffect: {
          brushType: 'stroke'
        },
        label: {
          normal: {
            show: true,
            position: 'right',
            formatter: '{b}',
            color: isDark ? '#fff' : '#333',
            fontSize: 10
          }
        },
        symbolSize: 8,
        itemStyle: {
          normal: {
            color: mainColor
          }
        },
        data: points
      }
    ]
  };

  myMap.setOption(option);
};

// 3. 初始化普通图表
const initCharts = () => {
  const isDark = props.isDarkMode;
  const textColor = isDark ? '#cbd5e1' : '#475569';
  const mainColor = themeColor.value || '#1E88E5';

  // --- 趋势图 (Line) ---
  myTrend = echarts.init(trendChart.value);
  myTrend.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 30, right: 20, bottom: 20, left: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月'],
      axisLine: { lineStyle: { color: isDark ? '#475569' : '#cbd5e1' } },
      axisLabel: { color: textColor }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: isDark ? '#334155' : '#e2e8f0' } },
      axisLabel: { color: textColor }
    },
    series: [{
      data: [1, 3, 2, 5, 4, 8],
      type: 'line',
      smooth: true,
      symbol: 'none',
      itemStyle: { color: mainColor },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: mainColor },
          { offset: 1, color: isDark ? 'rgba(0,0,0,0)' : 'rgba(255,255,255,0)' }
        ]),
        opacity: 0.2
      }
    }]
  });

  // --- 柱状图 (Bar) ---
  myBar = echarts.init(barChart.value);
  myBar.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 10, right: 20, bottom: 20, left: 10, containLabel: true },
    xAxis: {
      type: 'value',
      show: false
    },
    yAxis: {
      type: 'category',
      data: ['武汉', '重庆', '上海', '北京'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: textColor, fontWeight: 'bold' }
    },
    series: [{
      type: 'bar',
      data: [3, 5, 8, 12],
      barWidth: 20,
      itemStyle: {
        borderRadius: [0, 10, 10, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: mainColor },
          { offset: 1, color: '#60A5FA' } // Lighter blue
        ])
      },
      label: {
        show: true,
        position: 'right',
        color: textColor
      }
    }]
  });
};

// --- Lifecycle ---
onMounted(() => {
  initMap();
  initCharts();
  
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  myMap?.dispose();
  myTrend?.dispose();
  myBar?.dispose();
});

const handleResize = () => {
  myMap?.resize();
  myTrend?.resize();
  myBar?.resize();
};

// 监听主题变化，重绘图表
watch(() => [isDarkMode.value, currentTheme.value], () => {
  renderMap(); // Map needs specific option rebuild
  initCharts(); // Charts simple rebuild
});

</script>

<style scoped>
/* 确保图表容器有高度 */
</style>