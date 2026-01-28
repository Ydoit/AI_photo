import { defineStore } from 'pinia'
import { photoStoreSetup } from './photoStore'

export const useSelectionStore = defineStore('selection', photoStoreSetup)
