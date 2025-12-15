<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive>
      <component :is="Component" :key="route.name" v-if="route.meta?.keepAlive" />
    </keep-alive>
    <component :is="Component" :key="route.name" v-if="!route.meta?.keepAlive" />
  </router-view>
</template>

<script setup>
// Root component with keep-alive support for route caching
// Only routes with meta.keepAlive: true will be cached
</script>

