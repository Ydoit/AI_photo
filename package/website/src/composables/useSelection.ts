import { ref, reactive, computed } from 'vue'

export function useSelection() {
  const isSelectionMode = ref(false)
  const selectedIds = reactive(new Set<string>())

  const enterSelectionMode = () => {
    isSelectionMode.value = true
  }

  const exitSelectionMode = () => {
    isSelectionMode.value = false
    selectedIds.clear()
  }

  const toggleSelectionMode = (val?: boolean) => {
    if (val !== undefined) {
      val ? enterSelectionMode() : exitSelectionMode()
    } else {
      isSelectionMode.value ? exitSelectionMode() : enterSelectionMode()
    }
  }

  const toggleSelect = (id: string) => {
    if (selectedIds.has(id)) {
      selectedIds.delete(id)
    } else {
      selectedIds.add(id)
    }
  }

  const selectAll = (ids: string[]) => {
    const allSelected = ids.every(id => selectedIds.has(id))
    if (allSelected) {
      // Deselect all provided ids
      ids.forEach(id => selectedIds.delete(id))
    } else {
      // Select all provided ids
      ids.forEach(id => selectedIds.add(id))
    }
  }
  
  const isSelected = (id: string) => selectedIds.has(id)

  return {
    isSelectionMode,
    selectedIds,
    enterSelectionMode,
    exitSelectionMode,
    toggleSelectionMode,
    toggleSelect,
    selectAll,
    isSelected
  }
}
