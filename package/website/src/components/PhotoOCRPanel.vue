<template>
  <div
    class="fixed inset-y-0 right-0 w-80 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 h-full overflow-y-auto transition-transform duration-300 z-[103] shadow-2xl"
    :class="{ 'translate-x-full': !visible, 'translate-x-0': visible }"
    @click.stop
  >
    <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between sticky top-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur z-10">
        <h3 class="font-bold text-gray-900 dark:text-white">文字识别结果</h3>
        <button @click="$emit('close')" class="p-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-200">
            <PanelRightClose class="w-4 h-4" />
        </button>
    </div>

    <div v-if="loading" class="p-8 flex justify-center">
        <Loader2 class="w-6 h-6 animate-spin text-primary-500" />
    </div>

    <div v-else-if="records.length === 0" class="p-8 text-center text-gray-400 text-sm">
        <ScanText class="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>暂无识别结果</p>
    </div>

    <div v-else class="p-4">
            <div
            v-for="rec in records"
            :key="rec.id"
            class="text-sm bg-gray-50 dark:bg-gray-800 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors mb-2 rounded-lg p-2"
            :class="{ 'border-primary-500 ring-1 ring-primary-500 bg-primary-50 dark:bg-primary-900/20': highlightedRecord?.id === rec.id }"
            @click="handleOCRClick(rec)"
        >
            <p class="text-gray-900 dark:text-gray-200 leading-relaxed">{{ rec.text }}</p>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
    PanelRightClose,
    Loader2,
    ScanText
} from 'lucide-vue-next'
import type { OCRRecord } from '@/api/ocr'
import { ElMessage } from 'element-plus'

interface Props {
  visible: boolean
  loading: boolean
  records: OCRRecord[]
  highlightedRecord: OCRRecord | null
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'click-record'])

const handleOCRClick = (record: OCRRecord) => {
    emit('click-record', record)

    // 复制到剪贴板（带完整容错+降级）
    if (record?.text) { // 先判断record.text是否存在
        const text = record.text.trim()
        if (!text) return ElMessage.warning('无可复制的文本')

        // 方案1：优先使用原生 Clipboard API（现代浏览器）
        if (navigator?.clipboard) { // 双层判断：navigator和clipboard都存在
            try {
                navigator.clipboard.writeText(text)
                ElMessage.success('复制成功')
            } catch (err) {
                // API调用失败，降级到方案2
                fallbackCopyToClipboard(text)
            }
        } 
        // 方案2：降级到document.execCommand（兼容旧浏览器/非安全上下文）
        else {
            fallbackCopyToClipboard(text)
        }
    }
}

// 降级复制方法（无依赖，兼容所有浏览器）
const fallbackCopyToClipboard = (text: string) => {
    // 创建隐藏的文本框
    const textArea = document.createElement('textarea')
    textArea.value = text
    // 避免滚动条/页面闪烁
    textArea.style.position = 'fixed'
    textArea.style.top = '-9999px'
    textArea.style.left = '-9999px'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)

    // 选中文本并复制
    textArea.select()
    textArea.setSelectionRange(0, text.length) // 兼容移动设备

    try {
        const isSuccess = document.execCommand('copy')
        if (isSuccess) {
            ElMessage.success('复制成功')
        } else {
            ElMessage.warning('复制失败，请手动选中文本复制')
        }
    } catch (err) {
        ElMessage.error('复制失败，请手动选中文本复制')
    } finally {
        // 无论成败，都移除临时文本框
        document.body.removeChild(textArea)
    }
}
</script>
