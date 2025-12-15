<template>
  <div class="fixed inset-0 z-[9999] pointer-events-none overflow-hidden" v-if="active">
    <canvas ref="canvasRef" class="w-full h-full"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

const props = defineProps<{
  active: boolean
}>()

const emit = defineEmits(['complete'])

const canvasRef = ref<HTMLCanvasElement | null>(null)

watch(() => props.active, (val) => {
  if (val) {
    requestAnimationFrame(explode)
  }
})

const explode = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const particles: any[] = []
  const particleCount = 100
  const centerX = window.innerWidth / 2
  const centerY = window.innerHeight / 2

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: centerX,
      y: centerY,
      vx: (Math.random() - 0.5) * 20,
      vy: (Math.random() - 0.5) * 20,
      life: 1,
      color: `hsl(${Math.random() * 360}, 70%, 50%)`
    })
  }

  const animate = () => {
    if (!ctx || !props.active) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    let alive = false
    particles.forEach(p => {
      if (p.life > 0) {
        alive = true
        p.x += p.vx
        p.y += p.vy
        p.life -= 0.02
        ctx.fillStyle = p.color
        ctx.globalAlpha = p.life
        ctx.beginPath()
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2)
        ctx.fill()
      }
    })

    if (alive) {
      requestAnimationFrame(animate)
    } else {
      emit('complete')
    }
  }

  animate()
}
</script>