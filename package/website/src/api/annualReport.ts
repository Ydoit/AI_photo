import type { AnnualReportData } from '@/types/annualReport';

// Mock Data
const MOCK_DATA: AnnualReportData = {
  year: new Date().getFullYear(),
  user: {
    nickname: '时光旅人',
    avatarUrl: '/avatar.png',
  },
  time: {
    totalPhotos: 2586,
    accompanyDays: 365,
    firstPhotoDate: '2024-01-01',
    lastPhotoDate: '2024-12-31',
    lateNightPhotoCount: 128,
  },
  memory: {
    categoryDistribution: [
      { name: '生活日常', value: 42 },
      { name: '旅行', value: 28 },
      { name: '人像', value: 20 },
      { name: '美食', value: 10 },
    ],
    topPersonCount: 342,
    topLocation: '杭州',
    maxPhotoDay: '2024-05-20',
    maxPhotoDayCount: 156,
    topFeature: '实况模式',
    topFeatureCount: 89,
  },
  emotion: {
    starredPhotos: 128,
    backupPhotos: 2586,
    totalOpenTimes: 1024,
    starredPhotosList: [
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
    ],
    sharedPhotosList: [
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
       `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
    ],
    emotionCarouselGroups: [
        {
            id: 'g1',
            locationName: '海边回忆',
            photos: [
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`
            ]
        },
        {
            id: 'g2',
            locationName: '城市漫步',
            photos: [
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`
            ]
        },
        {
            id: 'g3',
            locationName: '山野露营',
            photos: [
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
                `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`
            ]
        }
    ]
  },
  location: {
    lightenProvinceNum: 12,
    lightenCityNum: 35,
    topCities: [
        { cityName: '杭州', photoCount: 156, provinceName: '浙江' },
        { cityName: '成都', photoCount: 86, provinceName: '四川' },
        { cityName: '大理', photoCount: 42, provinceName: '云南' }
    ],
    locationPoints: [
        { lng: 120.15, lat: 30.28, name: '杭州', count: 156 },
        { lng: 104.06, lat: 30.67, name: '成都', count: 86 },
        { lng: 100.23, lat: 25.58, name: '大理', count: 42 },
        { lng: 116.40, lat: 39.90, name: '北京', count: 35 },
        { lng: 121.47, lat: 31.23, name: '上海', count: 28 },
        { lng: 113.26, lat: 23.13, name: '广州', count: 25 },
        { lng: 114.17, lat: 22.32, name: '香港', count: 18 },
        { lng: 108.93, lat: 34.27, name: '西安', count: 15 },
        { lng: 118.78, lat: 32.04, name: '南京', count: 12 },
        { lng: 112.98, lat: 28.19, name: '长沙', count: 10 },
        { lng: 110.33, lat: 20.03, name: '海口', count: 8 },
        { lng: 87.62, lat: 43.79, name: '乌鲁木齐', count: 6 }
    ]
  },
  season: {
    seasonList: [
      {
        seasonName: '春',
        photoCount: 68,
        topTag: '嫩芽',
        representativePhoto: `https://picsum.photos/seed/spring/400/600`,
        highlight: '和家人的18次春日野餐',
        shootMonth: '3-5月'
      },
      {
        seasonName: '夏',
        photoCount: 124,
        topTag: '蝉鸣',
        representativePhoto: `https://picsum.photos/seed/summer/400/600`,
        highlight: '26张海边落日的欢聚时刻',
        shootMonth: '6-8月'
      },
      {
        seasonName: '秋',
        photoCount: 92,
        topTag: '晚风',
        representativePhoto: `https://picsum.photos/seed/autumn/400/600`,
        highlight: '12张街头银杏的温柔定格',
        shootMonth: '9-11月'
      },
      {
        seasonName: '冬',
        photoCount: 45,
        topTag: '暖意',
        representativePhoto: `https://picsum.photos/seed/winter/400/600`,
        highlight: '8张围炉煮茶的冬日闲情',
        shootMonth: '12-2月'
      }
    ]
  },
  easterEgg: {
    bestPhotoUrl: `https://picsum.photos/seed/${Math.random().toString(36).substring(2)}/400/600`,
    bestPhotoDate: '2024-10-01',
    tags: {
      main: '生活记录家',
      sub: ['偏爱人像', '乐于收藏', '心怀温柔'],
    },
  },
};

export function getAnnualReport(): Promise<AnnualReportData> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_DATA);
    }, 800); // Simulate network delay
  });
}
