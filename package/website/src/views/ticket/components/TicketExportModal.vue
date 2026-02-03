<template>
  <el-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    title="导出车票数据"
    width="400px"
    destroy-on-close
  >
    <div class="flex flex-col gap-4 py-2">
      <p class="text-sm text-slate-500 dark:text-slate-400 mb-2">请选择您想要导出的文件格式：</p>
      
      <div v-if="hasSelectedTickets" class="mb-4 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-slate-700 dark:text-slate-200">批量导出样式 (仅针对 PNG)</span>
        </div>
        <el-radio-group 
          :model-value="selectedStyle"
          @change="$emit('update:selectedStyle', $event)"
          size="small" 
          class="w-full"
        >
          <el-radio-button label="blue">统一蓝色</el-radio-button>
          <el-radio-button label="red">统一红色</el-radio-button>
        </el-radio-group>
      </div>

      <div class="grid grid-cols-1 gap-3">
        <button 
          @click="$emit('execute', 'json')"
          class="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-all group"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-600 dark:text-orange-400">
              <Database class="w-5 h-5" />
            </div>
            <div class="text-left">
              <div class="font-bold text-slate-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">JSON 格式</div>
              <div class="text-xs text-slate-500">适合数据备份与恢复</div>
            </div>
          </div>
          <Download class="w-4 h-4 text-slate-400 group-hover:text-primary-500" />
        </button>

        <button 
          @click="$emit('execute', 'csv')"
          class="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/10 transition-all group"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400">
              <ListTree class="w-5 h-5" />
            </div>
            <div class="text-left">
              <div class="font-bold text-slate-800 dark:text-white group-hover:text-green-600 dark:group-hover:text-green-400">CSV 格式</div>
              <div class="text-xs text-slate-500">适合 Excel 查看与编辑</div>
            </div>
          </div>
          <Download class="w-4 h-4 text-slate-400 group-hover:text-green-500" />
        </button>

        <button 
          @click="$emit('execute', 'png')"
          :disabled="isBatchExporting"
          class="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/10 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-600 dark:text-purple-400">
              <div v-if="isBatchExporting" class="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <TicketIcon v-else class="w-5 h-5" />
            </div>
            <div class="text-left">
              <div class="font-bold text-slate-800 dark:text-white group-hover:text-purple-600 dark:group-hover:text-purple-400">仿真纸质票 (PNG)</div>
              <div class="text-xs text-slate-500">{{ isBatchExporting ? `导出中 ${exportProgress}%` : '将所选车票导出为仿真图片' }}</div>
            </div>
          </div>
          <Download class="w-4 h-4 text-slate-400 group-hover:text-purple-500" />
        </button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { Database, ListTree, Download, Ticket as TicketIcon } from 'lucide-vue-next';

defineProps<{
  show: boolean;
  hasSelectedTickets: boolean;
  selectedStyle: 'red' | 'blue';
  isBatchExporting: boolean;
  exportProgress: number;
}>();

defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'update:selectedStyle', value: 'red' | 'blue'): void;
  (e: 'execute', format: 'json' | 'csv' | 'png'): void;
}>();
</script>
