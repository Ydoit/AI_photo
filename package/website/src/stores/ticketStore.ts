import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useStorage } from '@vueuse/core';
import type { TicketBackend, TicketQueryParams } from '@/types/ticket';
import { ticketService } from '@/api/ticketService';
import { railwayService, type TicketStats, type TicketItem } from '@/api/railway';

export const useTicketStore = defineStore('ticket', () => {
  // --- State Persistence (LocalStorage) ---
  // 视图模式
  const viewMode = useStorage<'timeline' | 'grid'>('ticket-view-mode', 'timeline');
  // 筛选状态
  const filterType = useStorage<'all' | 'highspeed' | 'normal'>('ticket-filter-type', 'all');
  const sortType = useStorage<'date' | 'distance' | 'duration' | 'price'>('ticket-sort-type', 'date');
  const selectedPassenger = useStorage<string>('ticket-selected-passenger', '');

  // 搜索状态
  const searchQuery = useStorage<string>('ticket-search-query', '');
  
  // 统计数据缓存 (ID -> Stats)
  const statsMap = useStorage<Record<string, TicketStats>>('ticket-stats-map', {});

  // --- Data Cache (In-Memory) ---
  const tickets = ref<TicketBackend[]>([]);
  const lastFetchTime = ref<number>(0);
  const loading = ref(false);
  const error = ref('');

  // 缓存配置
  const CACHE_DURATION = 5 * 60 * 1000; // 5分钟缓存

  // --- Actions ---

  /**
   * 批量获取统计数据并更新缓存
   */
  async function fetchAndCacheStats() {
    if (tickets.value.length === 0) return;

    try {
      const items: TicketItem[] = tickets.value.map(t => ({
        id: String(t.id),
        train_code: t.train_code,
        departure_station: t.departure_station,
        arrival_station: t.arrival_station,
        date_time: t.date_time
      }));

      const res = await railwayService.getBatchStats(items);
      if (res.code === 200 && res.data) {
        // 更新缓存
        const newMap = { ...statsMap.value };
        res.data.forEach(stat => {
          if (stat.id) {
            newMap[stat.id] = stat;
          }
        });
        statsMap.value = newMap;
      }
    } catch (err) {
      console.error('Failed to fetch batch stats:', err);
      // 不抛出错误，以免影响主流程，仅记录日志
    }
  }

  /**
   * 获取车票数据
   * @param force 是否强制刷新
   */
  async function fetchTickets(force = false) {
    // 检查缓存是否有效
    const now = Date.now();
    const isCacheValid = now - lastFetchTime.value < CACHE_DURATION;

    if (!force && isCacheValid && tickets.value.length > 0) {
      return;
    }

    loading.value = true;
    error.value = '';

    try {
      const params: TicketQueryParams = {
        skip: 0,
        limit: 100,
        // 获取所有数据，在前端进行筛选
        // name: selectedPassenger.value || undefined,
      };

      const res = await ticketService.getTickets(params);
      tickets.value = res.items || [];
      lastFetchTime.value = now;
      
      // 获取车票后，自动触发统计数据更新
      // 不等待其完成，异步执行
      fetchAndCacheStats();
      
    } catch (err: any) {
      error.value = err.response?.data?.detail || '获取车票失败，请重试';
      console.error('Fetch tickets error:', err);
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * 手动刷新数据
   */
  async function refreshData() {
    await fetchTickets(true);
  }

  /**
   * 重置所有筛选和搜索状态
   */
  function resetFilters() {
    searchQuery.value = '';
    filterType.value = 'all';
    selectedPassenger.value = '';
    // sortType.value = 'date'; // 排序通常不需要重置，或者看需求
  }

  /**
   * 更新单条车票数据 (用于编辑/新增后的本地更新，避免立即全量刷新)
   * 当然也可以选择直接调用 refreshData()
   */
  function updateLocalTicket(ticket: TicketBackend) {
    const index = tickets.value.findIndex(t => t.id === ticket.id);
    if (index !== -1) {
      tickets.value[index] = ticket;
    } else {
      tickets.value.unshift(ticket);
    }
    // 数据变更，更新缓存时间或保持不变？
    // 如果手动修改了数据，建议视为最新
    lastFetchTime.value = Date.now();
  }

  function removeLocalTickets(ids: number[]) {
    tickets.value = tickets.value.filter(t => !ids.includes(t.id));
    lastFetchTime.value = Date.now();
  }

  return {
    // State
    viewMode,
    filterType,
    sortType,
    selectedPassenger,
    searchQuery,
    tickets,
    loading,
    error,
    lastFetchTime,
    statsMap,
    
    // Actions
    fetchTickets,
    refreshData,
    resetFilters,
    updateLocalTicket,
    removeLocalTickets,
    fetchAndCacheStats
  };
});
