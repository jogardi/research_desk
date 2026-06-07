<template>
    <q-card>
      <q-tabs v-model="tab" dense class="text-grey" active-color="secondary" indicator-color="secondary" align="justify" narrow-indicator>
        <q-tab v-for="tabItem in tabs" :key="tabItem.name" :name="tabItem.name" :label="tabItem.label">
          <q-icon name="close" class="cursor-pointer" @click.stop="removeTab(tabItem.name)" />
        </q-tab>
      </q-tabs>
  
      <div class="q-pa-md">
        <q-btn label="Add Tab" @click="addTab" color="secondary" />
      </div>
  
      <q-separator />
  
      <q-tab-panels v-model="tab" animated>
        <q-tab-panel v-for="tabItem in tabs" :key="tabItem.name" :name="tabItem.name">
          <div class="text-h6">{{ tabItem.label }}</div>
          {{ tabItem.content }}
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const tab = ref('mails');
  const tabs = ref([
    { name: 'mails', label: 'Mails', content: 'Content for Mails' },
    { name: 'alarms', label: 'Alarms', content: 'Content for Alarms' },
    { name: 'movies', label: 'Movies', content: 'Content for Movies' }
  ]);
  
  function addTab() {
    const newTabName = `newtab${tabs.value.length + 1}`;
    tabs.value.push({ name: newTabName, label: `Tab ${tabs.value.length}`, content: `Content for Tab ${tabs.value.length}` });
    tab.value = newTabName; // Optional: switch to the new tab immediately
  }
  
  function removeTab(tabName) {
    const index = tabs.value.findIndex(t => t.name === tabName);
    if (index !== -1) {
      tabs.value.splice(index, 1);
      if (tab.value === tabName) {
        tab.value = tabs.value.length > 0 ? tabs.value[tabs.value.length - 1].name : null;
      }
    }
  }
  </script>
  