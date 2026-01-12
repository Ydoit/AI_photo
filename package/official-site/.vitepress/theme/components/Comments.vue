<script setup lang="ts">
import Giscus from '@giscus/vue';
import { useData } from 'vitepress';

const { isDark, lang } = useData();
</script>

<template>
  <div style="margin-top: 24px">
    <Giscus
      id="comments"
      repo="LC044/TrailSnap"
      repoId="R_kgDOOnxH1A"
      category="Announcements"
      categoryId="DIC_kwDOOnxH1M4C0fso"
      mapping="pathname"
      term="Welcome to TrailSnap docs!"
      reactionsEnabled="1"
      emitMetadata="0"
      inputPosition="top"
      :theme="isDark ? 'dark' : 'light'"
      :lang="lang"
      loading="lazy"
    />
  </div>
</template>
