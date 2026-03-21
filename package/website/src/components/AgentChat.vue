<script setup lang="ts">
import { ref, onMounted, nextTick, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Bot, User, X, Loader2, Send } from 'lucide-vue-next';
import { agentApi } from '@/api/agent';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import PhotoLightbox from '@/components/PhotoLightbox.vue';

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

// Lightbox 状态
const isLightboxOpen = ref(false);
const currentPhotoSrc = ref<any>(null);
const currentPhotoIndex = ref(0);
const allPhotos = ref<any[]>([]);

// Markdown 解析器配置
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
});

// 自定义图片渲染以支持九宫格样式和前端代理路径
const getCorrectImageUrl = (src: string) => {
  if (!src) return '';
  if (src.startsWith('http') || src.startsWith('data:')) return src;

  let baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  if (baseUrl.endsWith('/')) {
    baseUrl = baseUrl.slice(0, -1);
  }

  if (!baseUrl) {
    // Development mode with Vite proxy
    if (src.startsWith('/medias')) return '/api' + src;
    if (src.startsWith('/api/')) return src;
    return '/api' + (src.startsWith('/') ? src : '/' + src);
  } else {
    // Production or custom base URL
    if (src.startsWith('/api/medias')) return baseUrl + src.replace('/api/', '/');
    if (src.startsWith('/medias')) return baseUrl + src;
    return baseUrl + (src.startsWith('/') ? src : '/' + src);
  }
};

md.renderer.rules.image = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const originalSrc = token.attrGet('src') || '';
  const alt = token.content || '';
  
  let src = getCorrectImageUrl(originalSrc);

  // 防御性补全由于拼接可能导致的双斜杠
  if (src.startsWith('http') && src.includes('//api/')) {
    src = src.replace('//api/', '/api/');
  }

  const fullSrc = src.replace('/thumbnail', '');

  return `<agent-image data-src="${src}" data-full-src="${fullSrc}" data-alt="${alt}"></agent-image>`;
};

// 拦截段落渲染
const defaultRender = md.renderer.rules.paragraph_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.paragraph_open = function(tokens, idx, options, env, self) {
  return defaultRender(tokens, idx, options, env, self);
};

const defaultParagraphClose = md.renderer.rules.paragraph_close || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.paragraph_close = function(tokens, idx, options, env, self) {
  return defaultParagraphClose(tokens, idx, options, env, self);
};

interface Message {
  role: 'user' | 'assistant';
  content: string;
  isMarkdown?: boolean;
}

const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '你好！我是 TrailSnap 智能相册助手。你可以问我：\n- "帮我整理一下最近拍的照片，写一段朋友圈文案"\n- "今年国庆节去了哪些地方？"\n- "找几张在海边的照片"',
    isMarkdown: false
  }
]);

const inputMessage = ref('');
const isLoading = ref(false);
const sessionId = ref('');
const messagesContainer = ref<HTMLElement | null>(null);

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const handleClose = () => {
  emit('update:modelValue', false);
};

const renderMarkdown = (content: string) => {
  let rawHtml = md.render(content);
  
  // 替换被 <p> 包裹的连续 <agent-image>
  rawHtml = rawHtml.replace(/<p>((?:\s*<agent-image[^>]*><\/agent-image>\s*)+)<\/p>/g, (match, p1) => {
    const imgs = p1.replace(/<agent-image data-src="([^"]+)" data-full-src="([^"]+)" data-alt="([^"]*)"><\/agent-image>/g, 
      '<div class="agent-gallery-item"><img src="$1" alt="$3" class="agent-gallery-image" data-full-src="$2" /></div>'
    );
    // 使用 CSS Grid 布局的容器
    return `<div class="agent-gallery-grid">${imgs}</div>`;
  });

  // 兜底散落的 <agent-image>
  rawHtml = rawHtml.replace(/<agent-image data-src="([^"]+)" data-full-src="([^"]+)" data-alt="([^"]*)"><\/agent-image>/g, 
      '<img src="$1" alt="$3" class="agent-gallery-image inline-image" data-full-src="$2" />'
  );

  rawHtml = rawHtml.replace(/<p>\s*<\/p>/g, '');

  return DOMPurify.sanitize(rawHtml, { 
    ADD_TAGS: ['img', 'div'], 
    ADD_ATTR: ['target', 'class', 'src', 'alt', 'data-full-src'] 
  });
};

const setupImageClick = () => {
  if (messagesContainer.value) {
    const images = messagesContainer.value.querySelectorAll('.agent-gallery-image');
    images.forEach(img => {
      const clone = img.cloneNode(true);
      if(img.parentNode) {
        img.parentNode.replaceChild(clone, img);
      }
      clone.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const target = e.target as HTMLImageElement;
        
        let originalSrc = target.getAttribute('data-full-src') || target.src.replace('/thumbnail', '');
        
        const imgElements = messagesContainer.value?.querySelectorAll('.agent-gallery-image');
        if (imgElements && imgElements.length > 0) {
          allPhotos.value = Array.from(imgElements).map((el, index) => {
            let photoSrc = el.getAttribute('data-full-src') || (el as HTMLImageElement).src.replace('/thumbnail', '');
            
            // Extract real photo ID from URL if possible, e.g., /api/medias/{uuid}
            let realId = `agent-img-${index}`;
            const idMatch = photoSrc.match(/\/medias\/([a-f0-9\-]{36})/i);
            if (idMatch && idMatch[1]) {
              realId = idMatch[1];
            }
            
            if (!photoSrc.startsWith('http') && !photoSrc.startsWith('data:')) {
               photoSrc = window.location.origin + (photoSrc.startsWith('/') ? photoSrc : '/' + photoSrc);
            }

            // Fix the photo url, change /medias/UUID to /medias/UUID/file if not already thumbnail or file
            if (!photoSrc.includes('/thumbnail') && !photoSrc.includes('/file')) {
                const match = photoSrc.match(/(\/medias\/[a-f0-9\-]{36})$/i);
                if (match) {
                    photoSrc = photoSrc + '/file';
                }
            }

            return { 
              id: realId, 
              url: photoSrc, 
              preview: photoSrc, 
              file_type: 'image' 
            };
          });
          const clickedIndex = Array.from(imgElements).indexOf(target);
          currentPhotoIndex.value = clickedIndex !== -1 ? clickedIndex : 0;
          currentPhotoSrc.value = allPhotos.value[currentPhotoIndex.value];
          isLightboxOpen.value = true;
        } else {
          let fallbackSrc = originalSrc;
          let realId = 'agent-img-0';
          const idMatch = fallbackSrc.match(/\/medias\/([a-f0-9\-]{36})/i);
          if (idMatch && idMatch[1]) {
            realId = idMatch[1];
          }
          if (!fallbackSrc.startsWith('http') && !fallbackSrc.startsWith('data:')) {
             fallbackSrc = window.location.origin + (fallbackSrc.startsWith('/') ? fallbackSrc : '/' + fallbackSrc);
          }
          
          if (!fallbackSrc.includes('/thumbnail') && !fallbackSrc.includes('/file')) {
              const match = fallbackSrc.match(/(\/medias\/[a-f0-9\-]{36})$/i);
              if (match) {
                  fallbackSrc = fallbackSrc + '/file';
              }
          }
          
          const singleImg = { id: realId, url: fallbackSrc, preview: fallbackSrc, file_type: 'image' };
          allPhotos.value = [singleImg];
          currentPhotoIndex.value = 0;
          currentPhotoSrc.value = singleImg;
          isLightboxOpen.value = true;
        }
      });
    });
  }
};

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;

  const userText = inputMessage.value.trim();
  messages.value.push({ role: 'user', content: userText });
  inputMessage.value = '';
  isLoading.value = true;
  await scrollToBottom();

  try {
    const res = await agentApi.chat({
      message: userText,
      session_id: sessionId.value || undefined
    });

    if (res.data) {
      if (res.data.session_id) {
        sessionId.value = res.data.session_id;
      }
      messages.value.push({ 
        role: 'assistant', 
        content: res.data.response,
        isMarkdown: true 
      });
    }
  } catch (error: any) {
    let errorMsg = '请求失败，请稍后再试';
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail;
    }
    ElMessage.error(errorMsg);
    messages.value.push({ 
      role: 'assistant', 
      content: `❌ ${errorMsg}` 
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
    setTimeout(setupImageClick, 100);
  }
};

onMounted(() => {
  if (props.modelValue) {
    scrollToBottom();
  }
});
</script>

<template>
  <div v-if="modelValue" class="agent-chat-overlay" @click.self="handleClose">
    <div class="agent-chat-container">
      <!-- Header -->
      <div class="agent-chat-header">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center">
            <Bot class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h3 class="font-semibold text-slate-800 dark:text-white text-sm m-0">TrailSnap</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400 m-0">您的智能相册管家</p>
          </div>
        </div>
        <button @click="handleClose" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Messages -->
      <div class="agent-chat-messages" ref="messagesContainer">
        <div 
          v-for="(msg, index) in messages" 
          :key="index"
          class="message-wrapper"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div v-if="msg.role === 'assistant'" class="message-avatar assistant">
            <Bot class="w-4 h-4" />
          </div>

          <div class="message-bubble" :class="msg.role">
            <div v-if="msg.isMarkdown" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
            <div v-else class="whitespace-pre-wrap">{{ msg.content }}</div>
          </div>

          <div v-if="msg.role === 'user'" class="message-avatar user">
            <User class="w-4 h-4" />
          </div>
        </div>

        <div v-if="isLoading" class="message-wrapper justify-start">
          <div class="message-avatar assistant">
            <Bot class="w-4 h-4" />
          </div>
          <div class="message-bubble assistant flex items-center gap-2 py-3">
            <Loader2 class="w-4 h-4 animate-spin text-indigo-500" />
            <span class="text-sm text-slate-500">思考中...</span>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="agent-chat-input-area">
        <form @submit.prevent="sendMessage" class="relative">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="问问我关于您的照片或行程..."
            class="agent-input"
            :disabled="isLoading"
          />
          <button 
            type="submit" 
            class="agent-send-btn"
            :disabled="!inputMessage.trim() || isLoading"
          >
            <Send class="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>

    <!-- 引入全屏图片预览组件 -->
    <PhotoLightbox
      v-model:visible="isLightboxOpen"
      :image="currentPhotoSrc"
      :hasPrev="currentPhotoIndex > 0"
      :hasNext="currentPhotoIndex < allPhotos.length - 1"
      @close="isLightboxOpen = false"
      @prev="() => { if (currentPhotoIndex > 0) { currentPhotoIndex--; currentPhotoSrc = allPhotos[currentPhotoIndex]; } }"
      @next="() => { if (currentPhotoIndex < allPhotos.length - 1) { currentPhotoIndex++; currentPhotoSrc = allPhotos[currentPhotoIndex]; } }"
    />
  </div>
</template>

<style scoped>
.agent-chat-overlay {
  @apply fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-black/20 backdrop-blur-sm sm:p-4;
}

.agent-chat-container {
  @apply w-full sm:w-[450px] sm:max-w-full h-[85vh] sm:h-[600px] max-h-screen bg-white dark:bg-slate-900 sm:rounded-2xl shadow-2xl flex flex-col overflow-hidden sm:border border-slate-200 dark:border-slate-800;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.agent-chat-header {
  @apply px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-white/80 dark:bg-slate-900/80 backdrop-blur-md z-10;
}

.agent-chat-messages {
  @apply flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth;
}

.message-wrapper {
  @apply flex items-end gap-2 w-full;
}

.message-avatar {
  @apply w-7 h-7 rounded-full flex items-center justify-center shrink-0 mb-1;
}

.message-avatar.assistant {
  @apply bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400;
}

.message-avatar.user {
  @apply bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400;
}

.message-bubble {
  @apply max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm;
}

.message-bubble.user {
  @apply bg-indigo-600 text-white rounded-br-sm;
}

.message-bubble.assistant {
  @apply bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-100 dark:border-slate-700 rounded-bl-sm;
}

.agent-chat-input-area {
  @apply p-4 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800;
}

.agent-input {
  @apply w-full pl-4 pr-12 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-800 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all;
}

.agent-send-btn {
  @apply absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors;
}

/* Markdown Styles */
:deep(.markdown-body) {
  @apply text-sm leading-relaxed;
}

:deep(.markdown-body p) {
  @apply mb-2 last:mb-0;
}

:deep(.markdown-body strong) {
  @apply font-semibold text-slate-900 dark:text-white;
}

:deep(.markdown-body ul) {
  @apply list-disc pl-5 mb-2;
}

/* Custom Gallery Layout for AI returned images (CSS Grid 布局) */
:deep(.agent-gallery-grid) {
  display: grid !important;
  /* 强制使用 CSS Grid 3列布局 */
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap: 4px !important;
  margin: 12px 0 !important;
  padding: 0 !important;
  background-color: transparent !important;
  width: 100%;
  box-sizing: border-box;
}

:deep(.agent-gallery-item) {
  position: relative;
  width: 100%;
  /* 经典的 1:1 占位法，保证图片不论多宽，高度都与宽度一致 */
  padding-bottom: 100%; 
  overflow: hidden;
  border-radius: 6px;
  background-color: rgb(241 245 249);
}

:deep(.dark .agent-gallery-item) {
  background-color: rgb(30 41 59);
}

:deep(.agent-gallery-image) {
  position: absolute;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  cursor: pointer;
  border: none !important;
  transition: filter 0.2s ease;
}

:deep(.agent-gallery-image.inline-image) {
  position: relative;
  width: auto !important;
  max-width: 100% !important;
  height: auto !important;
  border-radius: 8px;
}

:deep(.agent-gallery-item:hover .agent-gallery-image) {
  filter: brightness(0.85);
}
</style>
