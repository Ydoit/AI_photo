<template>
  <el-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    title="仿真纸质车票"
    destroy-on-close
    class="paper-ticket-dialog w-full md:w-[900px]"
  >
    <div class="flex flex-col items-center gap-6 py-4">
      <div class="w-full">
        <TrainTicket
          v-if="ticket"
          ref="paperTicketRef"
          :ticket="ticket"
          :ticket_style="selectedStyle"
        />
      </div>
      <div class="flex flex-col items-center gap-4">
        <div class="flex items-center gap-4 bg-slate-100 dark:bg-slate-700 p-2 rounded-lg">
          <span class="text-sm font-medium text-slate-600 dark:text-slate-300">票面样式：</span>
          <el-radio-group 
            :model-value="selectedStyle"
            @change="$emit('update:selectedStyle', $event)"
            size="small"
          >
            <el-radio-button label="blue">蓝票</el-radio-button>
            <el-radio-button label="red">红票</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="flex gap-4">
          <el-button type="primary" @click="handleExport">
            <Download class="w-4 h-4 mr-2" />
            导出为图片
          </el-button>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Download } from 'lucide-vue-next';
import TrainTicket from '@/components/TrainTicket.vue';
import type { TicketFrontend } from '@/types/ticket';

defineProps<{
  show: boolean;
  ticket: TicketFrontend | null;
  selectedStyle: 'red' | 'blue';
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
  (e: 'update:selectedStyle', value: 'red' | 'blue'): void;
  (e: 'export'): void;
}>();

const paperTicketRef = ref<any>(null);

const handleExport = () => {
  emit('export');
};
</script>
