<!-- src/layouts/LoginLayout.vue -->
<template>
  <q-layout view="hHh Lpr lFf" :class="$q.dark.isActive ? 'bg-grey-9 text-white' : 'bg-grey-4'">
    <q-header id="header" Xelevated :class="$q.dark.isActive ? 'bg-grey-8' : 'bg-grey-8'">
      <q-toolbar class="header-bg">
        <!-- Toolbar Logo and Title -->
        <q-toolbar-title>
          <div @click="reloadSite()"  class="flex items-center q-py-sm cursor-pointer">
            <!-- <img
              src="/logo.png"
              style="width: 50px; height: 50px; margin-right: 0px; Xmargin-top: 10px; border-radius: 50%;"
            > -->
            <span class="header-logo q-ml-sm">The Research Desk</span>
          </div>
        </q-toolbar-title>
        <q-space />
        <q-btn @click="toggleTheme()"
            :color="$q.dark.isActive ? 'orange-1' : 'black'" :icon="$q.dark.isActive ? 'wb_sunny' : 'nights_stay'"
             flat dense style="opacity: .8">
          </q-btn>
      </q-toolbar>
    </q-header>
    <q-page-container>
      <router-view /> <!-- This is where the login form will be rendered -->
    </q-page-container>
  </q-layout>
</template>

<script setup>
  import { ref } from 'vue'
  import { useQuasar } from 'quasar'
  import { useTheme } from 'src/composables/useTheme';

  const $q = useQuasar()
  $q.dark.set(true)

  const { theme, switchTheme } = useTheme();

  function toggleTheme() {
    let newTheme = null
    if ($q.dark.isActive) {
      newTheme = 'light-theme'
    } 
    else {
      newTheme = 'dark-theme'
    }
    switchTheme(newTheme)
  }

  function reloadSite() {
    window.location.replace('/');
  }
</script>

<style scoped>
.pinky {
  background-color: #90c9c3;
}
</style>
