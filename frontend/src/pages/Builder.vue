<template>
    <q-page class="q-px-md q-pt-sm">
      <div class="page-flex-container">
        <!-- <div class="text-h6 q-mb-md">Knowledge Base Categories</div> -->
        <q-toolbar class="q-pa-none">
          <q-toolbar-title>KnowledgeBase - Builder</q-toolbar-title>
        </q-toolbar>
  
        <!-- Check/Uncheck a category -->
        
        <div class="flex justify-between">
            <!-- <div class="text-subtitle1 q-my-sm text-teal-3" with>Click Submit to generate/re-generate the database for the selected categories <q-icon name="east" size="sm"></q-icon></div> -->
            <!-- <q-btn @click="submit()" label="Submit" icon="settings" :disable="builderStore.builderSelectedCategoryIDs.length == 0" dense color="primary" class="q-mr-sm">
            </q-btn> -->
        </div>

        <!-- Toolbar -->
        <q-bar class="bg-grey-8">
          <q-space />

           <!-- Buttons Toolbar -->
          <div class="q-gutter-sm">
            <tooltip-btn tooltip="Start Database Generation" 
              @click="startGeneration" :disable="loading || builderStore.builderSelectedCategoryIDs.length == 0"
              icon="power" color="secondary">
            </tooltip-btn>
            <tooltip-btn tooltip="Abort Database Generation" 
              @click="abortGeneration" :disable="!loading"
              icon="power_off" color="red-3">
            </tooltip-btn>
            <tooltip-btn :tooltip="`${statusMessage == ''? 'Show' : 'Refresh'} Status`" @click="checkStatus"
              :icon="statusMessage == ''? 'visibility' : 'refresh'" color="primary" >
            </tooltip-btn>

            <!-- Processing ... spinner -->
            <span v-if="loading" class="text-info">
              <q-spinner-audio thickness="10" size="sm"/> <span>Processing ...</span>
            </span>
          </div>
      </q-bar>

      <!-- Database Generation Status Card -->
      <q-card v-if="statusMessage" class="q-mt-md">
        <div class="flex justify-between q-pa-sm">
          <span class="text-subtitle1 text-teal-3">Database Generation Status</span>
          <q-btn icon="close" @click="statusMessage = ''" flat color="primary" dense class="q-pr-sm"></q-btn>
        </div>
        <q-separator />
        <q-card>
          <q-card-section>
            <pre>{{ statusMessage }}</pre>
          </q-card-section>
        </q-card>
      </q-card>
      
        <!-- Category Tree -->
        <div class="text-subtitle1 q-pt-md">Select Categories:</div>
        <q-separator spaced style="width: 65%;" />

        <div ref="listContainer" v-if="categories.length > 0" :style="`height: ${remainingHeight}px; overflow-y: scroll;`"
            class="Xtree-container q-pb-sm q-px-md">
          <q-tree @update:ticked="handleTicked()"
            color="primary"
            ref="categoryTree"
            :nodes="categories"
            node-key="id"
            label="label"
            tick-strategy="leaf"
            v-model:ticked="builderStore.builderSelectedCategoryIDs"
            default-expand-all
          />
          <q-separator spaced style="width: 65%;" />
        </div>
      </div>
    </q-page>
  
    <q-drawer side="right" Xdark bordered :class="$q.dark.isActive ? 'bg-grey-10' : 'bg-grey-9'" class="q-pa-md"
        v-model="leftDrawerOpen"
        show-if-above
        :width="400"
      >
      </q-drawer>
</template>
  
  <script setup>
    import { ref, onMounted, onUnmounted, onBeforeMount, nextTick } from 'vue'
    
    import { AppFullscreen, useQuasar } from 'quasar'
    import { useBuilderStore } from 'src/stores/builder-store';
    import { Config } from 'src/config.js';
    import TooltipBtn from 'src/components/TooltipBtn.vue'
    import SelectedCategories from 'src/components/SelectedCategories.vue'
    import useResizeToFill from 'src/composables/useResizeToFill';
  
    const builderStore = useBuilderStore()

    const $q = useQuasar() 
    const leftDrawerOpen = ref(false)

    const { listContainer, remainingHeight } = useResizeToFill(35);
  
    // Category Tree
    const categories = ref([]); // the tree nodes data
    const selected = ref('') // not used
    const categoryTree = ref(null) // ref('categoryTree') - to access the tree object

    const loading = ref(false);
    const statusMessage = ref('');
    const status = ref(''); 
    let pollingInterval = null;

    onMounted(() => {
      pollingInterval = setInterval(checkIsRunning, 5000);
      checkIsRunning();
    });

    onBeforeMount(async () => {
      categories.value = await builderStore.loadBuilderCategories();
      handleTicked();
    });

    onUnmounted(() => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    });

    const checkIsRunning = async () => {
    try {
      const response = await fetch(`${Config.API_SERVER}/api/generate_databases/is-running`, {
        method: 'GET',
        credentials: 'include'
      });
      const data = await response.json();
      loading.value = data.isRunning;
      // if (!data.isRunning) {
      //   clearInterval(pollingInterval);
      //   pollingInterval = null;
      // }
    } 
    catch (error) {
      console.error('Error checking if process is running:', error);
    }
  };
  
  async function startGeneration() {
    loading.value = true;
    statusMessage.value = '';
    // status.value = '';
    // status.value = 'Generation Running ...'
    try {
      const response = await fetch(`${Config.API_SERVER}/api/generate_databases/start`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ categoryIDs: builderStore.builderSelectedCategoryIDs }) // Example category IDs
      });
      const data = await response.json();
      console.log(data.message);
      // pollingInterval = setInterval(checkIsRunning, 2000);
    } 
    catch (error) {
      console.error('Failed to start generation:', error);
    }
  }
  
  async function abortGeneration() {
    try {
      const response = await fetch(`${Config.API_SERVER}/api/generate_databases/abort`, {
        method: 'POST',
        credentials: 'include'
      });
      const data = await response.json();
      console.log(data.message);
      $q.notify({
        message: 'Server will finish processing current category before aborting! Please wait ...',
        position: 'center',
        textColor: 'teal-3',
        multiLine: true,
        classes: 'text-subtitle1',
        icon: 'info'
        // type: 'positive'
      })

      // loading.value = false; 
      // if (pollingInterval) {
      //   clearInterval(pollingInterval);
      //   pollingInterval = null;
      // }
    }
    catch (error) {
      console.error('Failed to abort generation:', error);
    }
  }
  
  async function checkStatus() {
    try {
      const response = await fetch(`${Config.API_SERVER}/api/generate_databases/status`, {
        method: 'GET',
        credentials: 'include'
      });
      const data = await response.json();
      statusMessage.value = JSON.stringify(data, null, 2);
      // loading.value = data.isRunning;
      // if (!data.isRunning) {
      //   if (pollingInterval) {
      //     clearInterval(pollingInterval);
      //     pollingInterval = null;
      //   }
      // }
    } 
    catch (error) {
      console.error('Failed to check status:', error);
      statusMessage.value = 'Failed to check status.';
    }
  }

  function handleTicked() {
    builderStore.builderCategoryPaths = []; // Reset current labels
    nextTick(() => {
      builderStore.builderSelectedCategoryIDs.forEach(id => {
        const path = _findPath(categories.value, id); // Find the path for each ticked node
        if (path) {
            // const pathStr = path.slice(1).join('/'); // Remove the root node from the path and join the path parts
            const pathStr = path.join('/'); // join the path parts
            builderStore.builderCategoryPaths.push(pathStr); // Add the path to the labels
        }
        });
        // sort labels:
        builderStore.builderCategoryPaths.sort((a, b) => a.localeCompare(b));
    });
}

function _findPath(nodes, id, path = []) {
  for (const node of nodes) {
    // Current path for this iteration
    const currentPath = [...path, node.label]; // Add the current node to the path

    if (node.id === id) {
      // Return the path when the node is found
      return currentPath;
    } 
    else if (node.children && node.children.length > 0) {
      // Continue searching in children
      const resultPath = _findPath(node.children, id, currentPath);
      if (resultPath) {
        return resultPath; // Return the found path
      }
    }
  }
  return null; // Return null if the node is not found
}
  </script>
  
  <style scoped>
    .page-flex-container {
    display: flex;
    flex-direction: column;
    height: 100vh; /* Make it fill the full viewport height */
    overflow: hidden; /* Prevent the page from scrolling */
  }
  
  .tree-container {
    flex-grow: 1; /* Allow this container to expand and fill available space */
    overflow-y: auto; /* Make only this container scrollable */
  }
  
  </style>