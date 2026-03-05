<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300 p-4 pb-10">
    
    <div class="max-w-[1400px] mx-auto mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button 
          @click="router.back()" 
          class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm"
        >
          <ArrowLeft class="w-4 h-4" />
          <span>返回列表</span>
        </button>
        <h1 class="text-2xl font-light text-slate-800 dark:text-white tracking-wide">
          旅行足迹报告
        </h1>
      </div>
      
      <div class="flex items-center gap-2 bg-white dark:bg-slate-800 rounded-lg p-1 border border-slate-200 dark:border-slate-700">
        <span class="px-3 py-1 text-xs font-medium text-slate-500 dark:text-slate-400 self-center">年份</span>
        <select v-model="selectedYear" class="px-3 py-1 text-xs bg-transparent text-slate-700 dark:text-slate-200 outline-none">
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
        </select>
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
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
            <div class="w-8 h-8 border-4 border-slate-200 dark:border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
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
              最北到达 
              <span 
                class="text-emerald-600 dark:text-emerald-400 font-bold"
                :title="northCities.length ? northCities.map(c => `${c.name}(${c.lon.toFixed(6)}, ${c.lat.toFixed(6)})`).join('；') : ''"
              >
                {{ northCities.length ? northCities.map(c => c.name).join('、') : '未知' }}
              </span>
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
              <span class="text-4xl font-bold text-slate-800 dark:text-white font-mono">{{ totalStats.days }}</span>
              <span class="text-sm text-slate-500">天</span>
            </div>
            <div class="mt-2 text-xs text-slate-400">
              去重乘车天数 <span class="text-purple-600 dark:text-purple-400 font-bold">{{ totalStats.days }}</span> 天
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
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 h-80 flex flex-col relative">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4">出行频率趋势</h3>
          <div ref="trendChart" class="flex-1 w-full"></div>
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
            <div class="w-8 h-8 border-4 border-slate-200 dark:border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
          </div>
          <div v-else-if="computeAggregates(selectedYear).monthlyCounts.reduce((a,b)=>a+b,0)===0" class="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
            暂无数据
          </div>
        </div>
        
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 h-80 flex flex-col relative">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-slate-800 dark:text-white">最爱去的城市</h3>
            <button @click="toggleShowAllCities" class="text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600">
              {{ showAllCities ? '收起' : '查看更多' }}
            </button>
          </div>
          <div ref="barChart" class="flex-1 w-full"></div>
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
            <div class="w-8 h-8 border-4 border-slate-200 dark:border-slate-700 border-t-primary-500 rounded-full animate-spin"></div>
          </div>
          <div v-else-if="computeAggregates(selectedYear).cityRanking.length===0" class="absolute inset-0 flex items-center justify-center text-slate-400 text-sm">
            暂无数据
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, computed } from 'vue';
import * as echarts from 'echarts';
import { ArrowLeft, Route, MapPin, Clock } from 'lucide-vue-next';
import { injectTheme } from '@/composables/useTheme';
import { useTicketStore } from '@/stores/ticketStore';
import { useStorage } from '@vueuse/core';
import { railwayService } from '@/api/railway';

// 接收父组件传入的主题和模式（移除未使用的props）

// 2. 注入全局状态
const { isDarkMode, currentTheme } = injectTheme();

// 3. 提取所需的响应式值
const themeColor = computed(() => currentTheme.value.primary);
defineEmits(['back']);

// --- DOM Refs ---
const mapContainer = ref<HTMLDivElement | null>(null);
const trendChart = ref<HTMLDivElement | null>(null);
const barChart = ref<HTMLDivElement | null>(null);
let myMap: echarts.ECharts | null = null;
let myTrend: echarts.ECharts | null = null;
let myBar: echarts.ECharts | null = null;

// --- 车票数据接入与统计 ---
import { useRouter } from 'vue-router';

const router = useRouter();
const ticketStore = useTicketStore();
const loading = ref(false);
const error = ref('');

const selectedYear = useStorage<number>('stats-selected-year', new Date().getFullYear());
const availableYears = ref<number[]>([selectedYear.value]);
const stationToCityMap = new Map<string, string>();

interface Aggregates {
  distance: number;
  cities: number;
  days: number;
  monthlyCounts: number[];
  cityRanking: { name: string; count: number }[];
  routes: { from: string; to: string }[];
  points: { name: string; value: [number, number, number] }[];
}
const cache = new Map<number, Aggregates>();
const missingLinearDistanceCache = new Map<number, number>();

const totalStats = ref({
  distance: 0,
  cities: 0,
  days: 0
});
const showAllCities = ref(false);

function getTicketYear(t: any): number {
  const s = String(t?.date_time || t?.datetime || t?.dateTime || '');
  const y = Number(s.slice(0, 4));
  return isFinite(y) ? y : 0;
}

function safeMileage(val: any): number {
  const n = Number(val);
  if (!isFinite(n) || isNaN(n)) return 0;
  if (n < 0) return 0;
  if (n > 1000000) return 0;
  return n;
}

// --- 城市经纬度字典 (核心：ECharts 需要经纬度) ---
// 实际项目中建议后端返回或引入完整的城市坐标库
const cityCoords: Record<string, [number, number]> = {
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
  '乌鲁木齐': [87.616848, 43.825592],
  '南京': [118.796877, 32.060255],
  '长沙': [112.938814, 28.228209],
  '兰州': [103.834303, 36.061089],
  '柳州': [109.41552, 24.32543],
  '郑州': [113.665412, 34.757975],
  '济南': [117.000923, 36.675807],
  '合肥': [117.283042, 31.86119],
  '福州': [119.306239, 26.074507],
  '南宁': [108.320004, 22.82402],
  '昆明': [102.712251, 25.040609],
  '贵阳': [106.713478, 26.578343],
  '天津': [117.200983, 39.084158],
  '青岛': [120.38264, 36.067082],
  '厦门': [118.089425, 24.479834],
  '苏州': [120.619586, 31.299379],
  '宁波': [121.550357, 29.874556],
  '沈阳': [123.431475, 41.686982],
  '大连': [121.618622, 38.91459],
  '长春': [125.323544, 43.817072]
};

function computeFeatureCenter(feature: any): [number, number] | null {
  const geom = feature?.geometry;
  if (!geom) return null;
  const type = geom.type;
  const coords = geom.coordinates;
  let xs = 0, ys = 0, n = 0;
  if (type === 'Polygon' && Array.isArray(coords)) {
    const ring = coords[0];
    if (Array.isArray(ring)) {
      for (let i = 0; i < ring.length; i++) {
        const p = ring[i];
        if (Array.isArray(p) && p.length >= 2) {
          xs += Number(p[0]) || 0;
          ys += Number(p[1]) || 0;
          n += 1;
        }
      }
    }
  } else if (type === 'MultiPolygon' && Array.isArray(coords)) {
    const poly = coords[0];
    if (Array.isArray(poly)) {
      const ring = poly[0];
      if (Array.isArray(ring)) {
        for (let i = 0; i < ring.length; i++) {
          const p = ring[i];
          if (Array.isArray(p) && p.length >= 2) {
            xs += Number(p[0]) || 0;
            ys += Number(p[1]) || 0;
            n += 1;
          }
        }
      }
    }
  }
  if (n === 0) return null;
  return [xs / n, ys / n];
}

function buildCityCoordsFromGeojson(geojson: any) {
  const features = geojson?.features || [];
  for (const f of features) {
    const props = (f as any).properties || {};
    const name: string | undefined = props.name || props.fullname;
    let cp: [number, number] | undefined = props.cp || props.center;
    if ((!cp || cp.length < 2) && f?.geometry) {
      const c = computeFeatureCenter(f);
      if (c) cp = c;
    }
    if (name && Array.isArray(cp) && cp.length >= 2) {
      const norm = normalizeCity(name);
      cityCoords[norm] = [cp[0], cp[1]];
      if (name.endsWith('市')) {
        const alias = name.slice(0, -1);
        cityCoords[normalizeCity(alias)] = [cp[0], cp[1]];
      }
    }
  }
}

async function loadStations() {
  try {
    // 获取所有站点信息，用于站点到城市的映射
    // 由于站点较多，这里一次性获取 2000 条（覆盖绝大多数常用站点）
    const res = await railwayService.getStations({ page: 1, page_size: 2000 });
    if (res.code === 200 && res.data?.list) {
      res.data.list.forEach(s => {
        stationToCityMap.set(s.station_name, s.city);
      });
    }
  } catch (e) {
    console.error('Failed to load stations', e);
  }
}

// 站点到城市归一化
function normalizeCity(station: string): string {
  // 1. 优先使用后端返回的映射
  const cityFromBackend = stationToCityMap.get(station);
  if (cityFromBackend) {
    return cityFromBackend.replace('市', '');
  }

  // 2. 兜底使用硬编码的特殊映射
  const explicit: Record<string, string> = {
    '北京南': '北京', '北京北': '北京', '北京西': '北京', '北京朝阳': '北京', '北京大兴': '北京', '北京': '北京',
    '天津南': '天津', '天津西': '天津', '天津': '天津',
    '上海虹桥': '上海', '上海南': '上海', '上海西': '上海', '上海': '上海',
    '广州南': '广州', '广州北': '广州', '广州': '广州',
    '深圳北': '深圳', '深圳': '深圳',
    '成都东': '成都', '成都': '成都',
    '重庆北': '重庆', '重庆东': '重庆', '重庆西': '重庆', '重庆南': '重庆', '重庆': '重庆',
    '杭州东': '杭州', '杭州': '杭州',
    '西安北': '西安', '西安': '西安',
    '南京南': '南京', '南京': '南京',
    '长沙南': '长沙', '长沙': '长沙',
    '兰州西': '兰州', '兰州': '兰州',
    '哈尔滨': '哈尔滨', '拉萨': '拉萨', '乌鲁木齐': '乌鲁木齐',
    '青岛北': '青岛', '青岛': '青岛',
    '厦门北': '厦门', '厦门': '厦门',
    '苏州北': '苏州', '苏州': '苏州',
    '宁波东': '宁波', '宁波': '宁波',
    '沈阳北': '沈阳', '沈阳': '沈阳',
    '大连北': '大连', '大连': '大连',
    '长春西': '长春', '长春': '长春'
  };
  if (explicit[station]) return explicit[station];
  return (station || '').replace(/(东|西|南|北|虹桥|火车站)$/u, '') || station;
}

function computeAggregates(year: number): Aggregates {
  const cached = cache.get(year);
  // 我们想要实时性，所以如果 store 更新了，最好不要使用太久的缓存。
  // 但为了性能，可以暂时保留缓存逻辑，或者依赖 ticketStore 的响应性。
  // 这里的 cache 是组件内的 Map，如果 ticketStore 变了，selectedYear 变了，会重新计算。
  // 但是 cache.get(year) 会阻止重新计算。
  // 建议移除这个简单的 cache，或者确保 cache key 包含 ticketStore 的 version/timestamp。
  // 简单起见，移除 cache 检查，或者清空 cache on update。
  // if (cached) return cached;
  
  const tickets = (ticketStore.tickets || []).filter(t => getTicketYear(t) === year);
  let distance = 0;
  for (let i = 0; i < tickets.length; i++) {
    const t = tickets[i];
    // 优先使用 Store 中的 statsMap (精确计算值)
    if (t.id && ticketStore.statsMap && ticketStore.statsMap[t.id]) {
      distance += ticketStore.statsMap[t.id].distance_km;
    } else {
      distance += safeMileage((t as any).total_mileage);
    }
  }
  distance = Math.round(distance);
  const extraMissing = missingLinearDistanceCache.get(year) || 0;
  distance += Math.round(extraMissing);
  const daySet = new Set();
  tickets.forEach(t => {
    const date = (t.date_time || '').split(' ')[0];
    if (date) daySet.add(date);
  });
  const days = daySet.size;
  const citySet = new Set();
  tickets.forEach(t => {
    citySet.add(normalizeCity('departure_station' in t ? t.departure_station : t.departure_city));
    citySet.add(normalizeCity('arrival_station' in t ? t.arrival_station : t.arrival_city));
  });
  const cities = citySet.size;
  const monthlyCounts = Array(12).fill(0);
  tickets.forEach(t => {
    const m = Number((t.date_time || '').slice(5, 7));
    if (m >= 1 && m <= 12) monthlyCounts[m - 1] += 1;
  });
  const cityCountMap = new Map<string, number>();
  tickets.forEach(t => {
    const city = normalizeCity('arrival_station' in t ? t.arrival_station : t.arrival_city);
    cityCountMap.set(city, (cityCountMap.get(city) || 0) + 1);
  });
  const cityRanking = Array.from(cityCountMap.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
  const routes = tickets.map(t => ({
    from: normalizeCity('departure_station' in t ? t.departure_station : t.departure_city),
    to: normalizeCity('arrival_station' in t ? t.arrival_station : t.arrival_city)
  }));
  const pointSet = new Map<string, [number, number, number]>();
  routes.forEach(r => {
    const fc = cityCoords[r.from] || cityCoords[normalizeCity(r.from)];
    const tc = cityCoords[r.to] || cityCoords[normalizeCity(r.to)];
    if (fc) pointSet.set(r.from, [fc[0], fc[1], 10]);
    if (tc) pointSet.set(r.to, [tc[0], tc[1], 10]);
  });
  const points = Array.from(pointSet.entries()).map(([name, value]) => ({ name, value }));
  const result: Aggregates = { distance, cities, days, monthlyCounts, cityRanking, routes, points };
  cache.set(year, result);
  return result;
}

// 1. 准备地图数据 (Lines 和 Points)
const getMapData = () => {
  const { routes, points } = computeAggregates(selectedYear.value);
  const linesData: { coords: [[number, number], [number, number]] }[] = [];
  routes.forEach(route => {
    const fromCoord = cityCoords[route.from] || cityCoords[normalizeCity(route.from)];
    const toCoord = cityCoords[route.to] || cityCoords[normalizeCity(route.to)];
    if (fromCoord && toCoord) {
      linesData.push({ coords: [fromCoord, toCoord] });
    }
  });
  return { lines: linesData, points };
};

// 2. 初始化地图
const initMap = async () => {
  if (!mapContainer.value) return;

  myMap = echarts.init(mapContainer.value);

  try {
    const response = await fetch('/api/medias/geojson?level=city');
    const chinaJson = await response.json();
    echarts.registerMap('china', chinaJson);
    buildCityCoordsFromGeojson(chinaJson);

    renderMap();
  } catch (e) {
    console.error("Map load failed", e);
    // 可以在这里显示一个错误提示或者降级方案
  }
};

const renderMap = () => {
  if (!myMap) return;

  const { lines, points } = getMapData();
  const isDark = isDarkMode.value;
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
  if (!trendChart.value || !barChart.value) return;
  const isDark = isDarkMode.value;
  const textColor = isDark ? '#cbd5e1' : '#475569';
  const mainColor = themeColor.value || '#1E88E5';

  myTrend?.dispose();
  myBar?.dispose();
  myTrend = echarts.init(trendChart.value);
  myTrend.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { top: 30, right: 20, bottom: 20, left: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
      axisLine: { lineStyle: { color: isDark ? '#475569' : '#cbd5e1' } },
      axisLabel: { color: textColor }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: isDark ? '#334155' : '#e2e8f0' } },
      axisLabel: { color: textColor }
    },
    series: [{
      data: computeAggregates(selectedYear.value).monthlyCounts,
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

  myBar = echarts.init(barChart.value);
  const ranking = computeAggregates(selectedYear.value).cityRanking;
  const top = showAllCities ? ranking : ranking.slice(0, 5);
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
      data: top.map(i => i.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: textColor, fontWeight: 'bold' }
    },
    series: [{
      type: 'bar',
      data: top.map(i => i.count),
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
onMounted(async () => {
  loading.value = true;
  error.value = '';
  try {
    await loadStations();
    await ticketStore.fetchTickets();
    const years = Array.from(new Set(ticketStore.tickets.map(t => getTicketYear(t)).filter(y => isFinite(y) && y > 0))).sort((a, b) => b - a);
    availableYears.value = years.length ? years : [selectedYear.value];
    await ensureLinearDistancesForYear(selectedYear.value);
    const agg = computeAggregates(selectedYear.value);
    totalStats.value = { distance: agg.distance, cities: agg.cities, days: agg.days };
    initMap();
    initCharts();
  } catch (e) {
    const msg = (e as any)?.message || '加载失败';
    console.error('Load tickets failed', e);
    error.value = msg;
  } finally {
    loading.value = false;
  }
  
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

watch(() => [ticketStore.tickets, ticketStore.statsMap], async () => {
  cache.clear();
  missingLinearDistanceCache.clear();
  await ensureLinearDistancesForYear(selectedYear.value);
  const agg = computeAggregates(selectedYear.value);
  totalStats.value = { distance: agg.distance, cities: agg.cities, days: agg.days };
  renderMap();
  initCharts();
}, { deep: true });

watch(selectedYear, async () => {
  await ensureLinearDistancesForYear(selectedYear.value);
  const agg = computeAggregates(selectedYear.value);
  totalStats.value = { distance: agg.distance, cities: agg.cities, days: agg.days };
  renderMap();
  initCharts();
});

function toggleShowAllCities() {
  showAllCities.value = !showAllCities.value;
  initCharts();
}

const northCities = computed<{ name: string; lon: number; lat: number }[]>(() => {
  const pts = computeAggregates(selectedYear.value).points || [];
  const valid = pts
    .map(p => {
      const v = Array.isArray(p.value) ? p.value : [NaN, NaN];
      const lon = Number(v[0]);
      const lat = Number(v[1]);
      return { name: String(p.name || ''), lon, lat };
    })
    .filter(p => isFinite(p.lon) && isFinite(p.lat));
  if (!valid.length) return [];
  let maxLat = -Infinity;
  for (const p of valid) {
    if (p.lat > maxLat) maxLat = p.lat;
  }
  const eps = 1e-9;
  return valid.filter(p => Math.abs(p.lat - maxLat) <= eps);
});

async function ensureLinearDistancesForYear(year: number) {
  if (missingLinearDistanceCache.has(year)) return;
  const tickets = (ticketStore.tickets || []).filter(t => {
    const y = getTicketYear(t);
    // 如果 statsMap 中有数据，则不需要降级计算直线距离
    if (t.id && ticketStore.statsMap && ticketStore.statsMap[t.id] && ticketStore.statsMap[t.id].distance_km > 0) {
      return false;
    }
    const d = Number(t.total_mileage || 0);
    return y === year && (!isFinite(d) || d <= 0);
  });
  const pairs = tickets.map(t => ({
    from: 'departure_station' in t ? t.departure_station : t.departure_city,
    to: 'arrival_station' in t ? t.arrival_station : t.arrival_city
  }));
  if (!pairs.length) {
    missingLinearDistanceCache.set(year, 0);
    return;
  }
}

</script>

<style scoped>
/* 确保图表容器有高度 */
</style>
