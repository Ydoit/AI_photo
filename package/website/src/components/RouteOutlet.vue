<!-- src/components/RouteOutlet.vue -->
<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive>
      <component :is="Component" v-if="route.meta.keepAlive" :key="route.path" />
    </keep-alive>
    <component :is="Component" v-if="!route.meta.keepAlive" :key="route.path" />
  </router-view>
</template>

<script setup lang="ts"></script>