<template>
    <div
    class="relative w-12 aspect-square rounded-full overflow-hidden border-2 transition-all duration-300 bg-gray-100 dark:bg-gray-800"
    :class="['border-transparent group-hover:border-gray-300 dark:group-hover:border-gray-600']"
    >
        <img
            v-if="person.cover_photo"
            :src="getPhotoUrl(person.cover_photo.photo_id)"
            class="absolute max-w-none transition-transform duration-500 group-hover:scale-110"
            :style="getFaceCropStyle(person.cover_photo)"
            loading="lazy"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
            <User class="w-1/2 h-1/2" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Search, Plus, User } from '@element-plus/icons-vue'
import type { PhotoMetadata, AlbumImage, CoverPhotoInfo, FaceIdentity } from '@/types/album'

const props = defineProps({
  person: {
    type: Object as () => FaceIdentity,
    default: () => ({})
  }
})

const getPhotoUrl = (photoId: string) => {
  return `/api/medias/${photoId}/thumbnail`
}

/**
 * 核心算法：计算人脸裁切样式
 */
const getFaceCropStyle = (cover: CoverPhotoInfo) => {
  if (!cover.face_rect || !cover.width || !cover.height) {
    return {}
  }

  // face_rect: [x1, y1, x2, y2]
  const [x1, y1, x2, y2] = cover.face_rect
  const faceW = x2 - x1
  const faceH = y2 - y1

  // 1. 确定裁切基准（取人脸宽高的最大值，并增加 60% 的留白防止太挤）
  const cropSize = Math.max(faceW, faceH) * 1.6

  // 2. 计算缩放比例：容器宽度 / 裁切目标在原图中的宽度
  // 这里直接用百分比：(原图宽 / 裁切宽) * 100%
  const widthPct = (cover.width / cropSize) * 100
  const heightPct = (cover.height / cropSize) * 100

  // 3. 计算人脸中心点坐标（百分比）
  const centerX = (x1 + x2) / 2
  const centerY = (y1 + y2) / 2
  const leftPct = (centerX / cover.width) * 100
  const topPct = (centerY / cover.height) * 100

  return {
    width: `${widthPct.toFixed(2)}%`,
    height: `${heightPct.toFixed(2)}%`,
    left: '50%',
    top: '50%',
    // 将图片中心移动到容器中心，再根据人脸中心点进行偏移
    transform: `translate(-${leftPct.toFixed(2)}%, -${topPct.toFixed(2)}%)`,
  }
}
</script>