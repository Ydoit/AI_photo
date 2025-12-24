import { defineStore } from 'pinia';
import { useStorage } from '@vueuse/core';

export const useLocationStore = defineStore('location', () => {
  // Persistent State
  const viewMode = useStorage<'grid' | 'map'>('trailsnap-location-view-mode', 'grid');
  const level = useStorage<'city' | 'province'>('trailsnap-location-level', 'city');

  return {
    viewMode,
    level
  };
});
