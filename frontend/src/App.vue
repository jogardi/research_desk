<template>
  <router-view />
</template>

<script setup>
import { onBeforeMount, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'src/stores/main-store'
import { useUserStore } from 'src/stores/user-store'

const store = useStore()
const userStore = useUserStore()
const router = useRouter()

onBeforeMount(async () => {
  const pagePath = window.location.pathname + window.location.search + window.location.hash;
  console.log(`*** App.vue - onBeforeMount: App.vue script is running (app load or reload) [Page: ${pagePath}] ***`);

  await store.initialize()
})
</script>
