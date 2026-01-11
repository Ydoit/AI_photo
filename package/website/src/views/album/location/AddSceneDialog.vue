<template>
  <el-dialog
    v-model="visible"
    title="新增景区"
    width="900px"
    destroy-on-close
    :close-on-click-modal="false"
    @open="initMap"
    @closed="resetForm"
  >
    <div class="flex gap-4 h-[600px]">
      <!-- Form -->
      <div class="w-1/3 flex flex-col gap-4 overflow-y-auto pr-2">
        <el-form :model="form" label-position="top">
          <el-form-item label="景区名称" required>
            <el-autocomplete
              v-model="form.name"
              :fetch-suggestions="querySearch"
              placeholder="输入景区名称"
              @select="handleSelect"
              class="w-full"
              :trigger-on-focus="false"
            >
              <template #default="{ item }">
                <div class="flex flex-col leading-tight py-1">
                  <span class="font-medium">{{ item.value }}</span>
                  <span class="text-xs text-gray-500">{{ item.address }}</span>
                </div>
              </template>
            </el-autocomplete>
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" />
          </el-form-item>
          <el-form-item label="等级（1-5）A">
            <el-rate v-model="form.level" :max="5" />
          </el-form-item>
          <el-form-item label="地址">
            <el-input v-model="form.address" placeholder="输入地址" />
          </el-form-item>
          <el-form-item label="半径 (米)">
             <el-input-number v-model="form.radius" :min="0" />
          </el-form-item>
          <el-form-item label="经纬度">
             <div class="flex gap-2">
                <el-input v-model="form.latitude" placeholder="Lat" readonly />
                <el-input v-model="form.longitude" placeholder="Lng" readonly />
             </div>
          </el-form-item>
          <el-form-item label="多边形坐标 (点数)" v-if="form.polygon && form.polygon.length > 0">
             <el-input :model-value="`${form.polygon.length} 个顶点`" readonly />
             <div class="text-xs text-gray-400 mt-1 break-all max-h-20 overflow-y-auto">
                {{ JSON.stringify(form.polygon) }}
             </div>
          </el-form-item>
        </el-form>
        
        <div class="mt-auto flex flex-col gap-2">
             <div class="border-t pt-2 mt-2">
                <p class="text-sm font-bold mb-2">绘制范围</p>
                <div class="text-xs text-gray-500 mb-2">
                  1. 点击"开始绘制"<br>
                  2. 在地图上点击添加顶点<br>
                  3. 双击完成绘制
                </div>
                <div class="flex gap-2">
                   <el-button v-if="!isDrawing" @click="startDraw">开始绘制</el-button>
                   <el-button v-else @click="finishDraw">完成绘制</el-button>
                   <el-button @click="clearDraw">清除</el-button>
                </div>
             </div>
        </div>
      </div>

      <!-- Map -->
      <div class="w-2/3 relative rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
         <div id="add-scene-map" class="w-full h-full"></div>
      </div>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          保存
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import { loadMapScript } from '@/utils/mapLoader'
import { locationService } from '@/api/location'
import { ElMessage } from 'element-plus'
import type { SceneCreate } from '@/types/location'

declare const T: any

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
watch(() => props.modelValue, (val) => visible.value = val)
watch(visible, (val) => emit('update:modelValue', val))

const submitting = ref(false)
const isDrawing = ref(false)
const form = reactive({
  name: '',
  description: '',
  level: 0,
  address: '',
  latitude: 0,
  longitude: 0,
  radius: 0,
  polygon: [] as number[][]
})

let map: any = null
let currentPolygon: any = null
let drawPoints: any[] = []
let markers: any[] = []
let searchService: any = null
let autocompleteCallback: any = null

const initMap = async () => {
  await loadMapScript()
  nextTick(() => {
    // Always create new map instance to ensure proper rendering in dialog
    // Clean up old map if needed (though local variable usually suffices)
    const container = document.getElementById('add-scene-map')
    if (container) {
        container.innerHTML = '' // clear previous map
    }
    
    map = new T.Map('add-scene-map')
    map.centerAndZoom(new T.LngLat(104.195, 35.861), 4)
    map.enableScrollWheelZoom()
    
    map.addEventListener('click', onMapClick)
    map.addEventListener('dblclick', onMapDblClick)

    // Initialize LocalSearch
    searchService = new T.LocalSearch(map, {
        pageCapacity: 10,
        onSearchComplete: (result: any) => {
            parseSearchResult(result)
        }
    })
  })
}

const parseSearchResult = (result: any) => {
    const type = parseInt(result.getResultType())
    console.log('Search complete:', result,type)
    // Handle suggestions
    if (type === 4) {
        if (autocompleteCallback) {
             const suggests = result.getSuggests()
             if (suggests) {
                 const data = suggests.map((item: any) => ({
                     value: item.name,
                     address: item.address,
                     ...item
                 }))
                 autocompleteCallback(data)
             } else {
                 autocompleteCallback([])
             }
             autocompleteCallback = null
        }
        return
    }

    // Clear callback if not suggestion
    if (autocompleteCallback) {
        autocompleteCallback([])
        autocompleteCallback = null
    }

    // Handle POIs (Type 1)
    if (type === 1) {
        const pois = result.getPois()
        if (pois && pois.length > 0) {
            const first = pois[0]
            updateFormWithLocation(first.lonlat, first.address)
        } else {
            ElMessage.warning('未找到相关位置')
        }
    } 
    // Handle Area (Type 3)
    else if (type === 3) {
        const area = result.getArea()
        if (area && area.lonlat) {
             updateFormWithLocation(area.lonlat, form.address || area.name)
        }
    }
    // Handle Statistics (Type 2) - Ambiguous search
    else if (type === 2) {
         ElMessage.warning('搜索结果过于宽泛，请尝试更精确的名称')
    }
    // Fallback
    else {
         ElMessage.warning('未找到准确位置')
    }
}

const updateFormWithLocation = (lnglatStr: string, address: string) => {
    let lat, lng
    if (typeof lnglatStr === 'string') {
        const parts = lnglatStr.split(/[\s,]+/)
        lng = parseFloat(parts[0])
        lat = parseFloat(parts[1])
    } else {
        return
    }

    if (!isNaN(lat) && !isNaN(lng)) {
        const pt = new T.LngLat(lng, lat)
        map.centerAndZoom(pt, 14)
        if (address) form.address = address
        form.latitude = lat
        form.longitude = lng
        // 创建带名称和地址的标注
        const winHtml = "名称:" + form.name + "<br/>地址:" + address;
        const marker = new T.Marker(pt)
        map.clearOverLays()
        map.addOverLay(marker)
        // 添加信息窗口
        const infoWin = new T.InfoWindow(winHtml, {offset: new T.Point(0, -30)})
        marker.addEventListener("click", () => map.openInfoWindow(infoWin, pt))
        
        // Restore polygon if drawing was active or exists
        if (currentPolygon) map.addOverLay(currentPolygon)
    }
}

const querySearch = (queryString: string, cb: any) => {
    if (!queryString || !searchService) {
        cb([])
        return
    }
    autocompleteCallback = cb
    searchService.search(queryString, 4) // Type 4 for suggestions
}

const handleSelect = (item: any) => {
    // If the item has location info directly (unlikely for suggestions), use it
    // Otherwise, search for the specific name to get details
    // Suggestion items usually have name, address, but maybe not lat/lng
    
    // Trigger a normal search for the selected name to get coordinates
    // We don't set autocompleteCallback, so it falls to the "else" block in onSearchComplete
    searchService.search(item.value, 1)
}

const onMapClick = (e: any) => {
    if (isDrawing.value) {
        drawPoints.push(e.lnglat)
        const marker = new T.Marker(e.lnglat)
        markers.push(marker)
        map.addOverLay(marker)
        updatePolygon()
        // Save points
        if (drawPoints.length >= 3) {
            form.polygon = drawPoints.map((p: any) => [p.lat, p.lng])
            // Calculate center
            let latSum = 0, lngSum = 0
            drawPoints.forEach((p: any) => {
                latSum += p.lat
                lngSum += p.lng
            })
            if (form.latitude === 0 && form.longitude === 0){
                form.latitude = latSum / drawPoints.length
                form.longitude = lngSum / drawPoints.length
            }
        }
    }
}

const onMapDblClick = (e: any) => {
    if (isDrawing.value) {
        finishDraw()
    }
}

const updatePolygon = () => {
    if (currentPolygon) {
        map.removeOverLay(currentPolygon)
    }
    if (drawPoints.length > 0) {
        currentPolygon = new T.Polygon(drawPoints, {
            color: "blue", weight: 3, opacity: 0.5, fillColor: "#FFFFFF", fillOpacity: 0.5
        })
        map.addOverLay(currentPolygon)
    }
}

const startDraw = () => {
    isDrawing.value = true
    drawPoints = []
    if (currentPolygon) map.removeOverLay(currentPolygon)
    currentPolygon = null
    // Disable map double click zoom
    map.disableDoubleClickZoom()
}

const finishDraw = () => {
    isDrawing.value = false
    map.enableDoubleClickZoom()
    // Save points
    if (drawPoints.length >= 3) {
         form.polygon = drawPoints.map((p: any) => [p.lat, p.lng])
         // Calculate center
         let latSum = 0, lngSum = 0
         drawPoints.forEach((p: any) => {
             latSum += p.lat
             lngSum += p.lng
         })
         if (form.latitude === 0 && form.longitude === 0){
            form.latitude = latSum / drawPoints.length
            form.longitude = lngSum / drawPoints.length
         }
    }
}

const clearDraw = () => {
    isDrawing.value = false
    drawPoints = []
    if (currentPolygon) map.removeOverLay(currentPolygon)
    currentPolygon = null
    form.polygon = []
    map.enableDoubleClickZoom()
    // Remove markers
    markers.forEach(marker => map.removeOverLay(marker))
    markers = []
}

const resetForm = () => {
    form.name = ''
    form.description = ''
    form.level = 0
    form.address = ''
    form.latitude = 0
    form.longitude = 0
    form.radius = 0
    form.polygon = []
    clearDraw()
    map = null 
}

const handleSubmit = async () => {
    if(!form.name) return ElMessage.error('请输入名称')
    
    submitting.value = true
    try {
        const payload: SceneCreate = {
            ...form,
            level: form.level || undefined
        }
        await locationService.createScene(payload)
        ElMessage.success('添加成功')
        visible.value = false
        emit('success')
    } catch(e) {
        console.error(e)
        ElMessage.error('添加失败')
    } finally {
        submitting.value = false
    }
}
</script>
