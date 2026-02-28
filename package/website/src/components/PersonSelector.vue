<template>
  <el-dialog
    :model-value="visible"
    title="添加到人物相册"
    :width="dialogWidth"
    class="rounded-xl"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div class="flex flex-col gap-4">
      <el-input
        v-model="searchQuery"
        placeholder="搜索人物名称..."
        clearable
        prefix-icon="Search"
      />

      <div class="h-[300px] overflow-y-auto border rounded-md p-2" v-loading="loading">
        <div v-if="filteredPeople.length === 0 && !searchQuery" class="text-gray-400 text-center py-4">
          暂无人物数据
        </div>
        
        <div
          v-for="person in filteredPeople"
          :key="person.id"
          class="flex items-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded transition-colors"
          @click="selectPerson(person)"
        >
          <PersonAvatar :person="person" />
          <div class="flex flex-col">
            <span class="font-medium">{{ person.identity_name }}</span>
            <span class="text-xs text-gray-500">{{ person.face_count }} 张照片</span>
          </div>
        </div>

        <div
          v-if="showCreateOption"
          class="flex items-center p-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded transition-colors text-primary"
          @click="createPerson"
        >
          <div class="w-10 h-10 rounded-full flex items-center justify-center mr-3 bg-blue-100 text-blue-600">
            <el-icon><Plus /></el-icon>
          </div>
          <span class="font-medium">创建新人物 "{{ searchQuery }}"</span>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Search, Plus, User } from '@element-plus/icons-vue'
import PersonAvatar from '@/components/PersonAvatar.vue'
import { faceApi } from '@/api/face'
import type { FaceIdentity } from '@/types/album'
import { useWindowSize } from '@vueuse/core'
import type { PhotoMetadata, AlbumImage, CoverPhotoInfo, Tag } from '@/types/album'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'select', identity: FaceIdentity): void
}>()

const { width } = useWindowSize()
const dialogWidth = computed(() => width.value < 640 ? '90%' : '400px')

const searchQuery = ref('')
const people = ref<FaceIdentity[]>([])
const loading = ref(false)

const filteredPeople = computed(() => {
  if (!searchQuery.value) return people.value
  const query = searchQuery.value.toLowerCase()
  return people.value.filter(p => 
    p.identity_name && p.identity_name.toLowerCase().includes(query)
  )
})

const showCreateOption = computed(() => {
  return searchQuery.value && !filteredPeople.value.some(p => p.identity_name === searchQuery.value)
})

const loadPeople = async () => {
  loading.value = true
  try {
    // Load all named identities (limit 1000 for now)
    const res = await faceApi.listIdentities(1, 1000)
    people.value = res
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    searchQuery.value = ''
    loadPeople()
  }
})

const selectPerson = (person: FaceIdentity) => {
  emit('select', person)
  emit('update:visible', false)
}

const createPerson = async () => {
  if (!searchQuery.value) return
  try {
    loading.value = true
    const newPerson = await faceApi.createIdentity({
      identity_name: searchQuery.value
    })
    emit('select', newPerson)
    emit('update:visible', false)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>
