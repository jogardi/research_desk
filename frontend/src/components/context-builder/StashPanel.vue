<template>
  <el-container style="height: 100%">
    <el-header height="auto">
    <!-- Buttons Tollbar -->
    <q-bar class="toolbar q-pt-none Xbg-grey-8">
      <!-- All Checkbox -->
    <div v-if="sessionStore.session.stashDocs && sessionStore.session.stashDocs.length > 0" class="flex justify-between  text-subtitle1">
      <div style="opacity: .8">
          <q-btn v-if="checkedCount != excerptCount" @click="checkAll(true)" no-caps dense Xsize="sm"
            label="Check All" icon="check" flat color="primary" class="text-subtitle2 p-mr-2" />
          <q-btn v-if="checkedCount > 0" @click="checkAll(false);" label="Uncheck All" icon="remove_done" 
            dense flat color="primary" no-caps />
        </div>
    </div>
      <q-space />
      <span style="font-size: .8rem; opacity: .7;" class="q-mr-md">{{ hits }} excerpts</span>
      <div class="q-gutter-sm">
        <tooltip-btn @click="removeCheckedItems()" tooltip="Remove selected items" icon="delete" color="negative" :disabled="checkedCount == 0"></tooltip-btn>
        <tooltip-btn @click="moveToContextCheckedItems" tooltip="Move selected items to the context tab" icon="playlist_add" color="primary" :disabled="checkedCount == 0"></tooltip-btn>
      </div>
    </q-bar>
    <!-- <q-separator /> -->
    </el-header>
    <el-main class="p-pt-3">
    <!-- Document List -->
    <el-scrollbar height="100%">
      <div v-for="doc in sessionStore.session.stashDocs" :key="doc.documentID">
        <!-- Document Info -->
        <document-info :doc="doc" :updateCounts="updateCounts" />

        <!-- Excerpts List -->
        <q-list Xpadding dense class="list_container p-py-2 p-pl-3">
          <q-item v-for="excerpt, excerptIndex in doc.excerpts" :key="excerpt[0]" dense  clickable class="p-pl-3 p-py-2">
            <!-- Checkbox -->
            <q-item-section side top> 
              <div Xclass="p-mb-1">    
                <q-checkbox @update:model-value="onCheckboxClicked" v-model="excerpt[2].checked" dense size="xs" color="primary" style="opacity: .7 !important;" />
              </div>
            </q-item-section>
          
          <!-- Excerpt Text -->
          <q-item-section>
            <div class="p-d-flex p-justify-content-between p-align-items-center">
              <div class="chunk-text" v-html="excerpt[2].text" style="padding-bottom: 5px !important;"></div>                                  
            </div>
            <image-viewer :doc="doc" :excerpt="excerpt" />
          </q-item-section>

          <!-- Excerpt Menu -->
          <q-item-section side top>
            <q-btn flat dense round icon="more_vert" color="primary" class="q-mr-sm">
              <q-menu anchor="bottom right" self="top right" class="menu-bg">
                <q-list dense padding>
                  <menu-item @click="moveToContext(excerpt, doc)" icon="undo" color="primary">
                    Move to Context
                  </menu-item>
                  <menu-item @click="removeItem(excerpt, doc)" icon="delete" color="primary">
                    Remove
                  </menu-item>                    
                </q-list>
              </q-menu>
            </q-btn>
          </q-item-section> 
        </q-item>
      </q-list>
      <q-separator v-if="filteredChunks.length > 0" Xspaced/>
    </div>
    </el-scrollbar>
  </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import { useLlmStore } from 'src/stores/llm-store';
import TooltipBtn from 'src/components/TooltipBtn.vue'
import MenuItem from 'src/components/MenuItem.vue'
import useCheckAll from 'src/composables//useCheckAll';
import useUtils from 'src/composables/useUtils';
import DocumentInfo from 'src/components/context-builder/DocumentInfo.vue'
import { moveExcerpt, removeExcerpt, removeCheckedExcerpts, moveCheckedExcerpts, getDocumentsText } from 'src/utils/docUtils.js';
import ImageViewer from 'src/components/context-builder/ImageViewer.vue';
import { initializeTableSorting, removeEventListeners } from 'src/utils/tableSorter.js';

const store = useStore()
const sessionStore = useSessionStore();
const utils = useUtils()
const llmStore = useLlmStore()  

const $q = useQuasar()

const { checkedCount, excerptCount, onCheckboxClicked, checkAll, updateCounts } = useCheckAll('stash');

// Initialize table sorting when component is mounted and when content changes
onMounted(() => {
  nextTick(() => {
    initializeTableSorting();
  });
});

onUnmounted(() => {
  removeEventListeners();
});

  // Computed property: filtered chunks
  const filteredChunks = computed(() => {
    return sessionStore.session.chunks.filter(chunk => chunk.status == 'S');
  });

  async function moveToContextCheckedItems() {
    moveCheckedExcerpts(sessionStore.session.stashDocs, sessionStore.session.contextDocs);
    removeCheckedItems();
    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }
  
  function removeCheckedItems() {
    const removeDocsSet = removeCheckedExcerpts(sessionStore.session.stashDocs);
    // Remove documents that have no chunks left
    if (removeDocsSet.size > 0) {
      sessionStore.session.stashDocs = sessionStore.session.stashDocs.filter(doc => !removeDocsSet.has(doc.documentID));
    }
    checkAll(false);
  }

  async function moveToContext(srcExcerpt, srcDoc) {
    const destDoc = moveExcerpt(srcExcerpt, srcDoc, sessionStore.session.contextDocs); // move excerpt to context
    destDoc.title = null // update the title
    if (srcDoc.chunks.length == 0) {
      sessionStore.session.stashDocs = sessionStore.session.stashDocs.filter(doc => doc.documentID !== srcDoc.documentID); // remove the srcDoc from source docs
    }
    else { 
        srcDoc.title = null // update the title
      }
    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }

  async function removeItem(excerpt, doc) {
    removeExcerpt(excerpt, doc); // remove the excerpt from the doc
    if (doc.chunks.length == 0) {
      sessionStore.session.stashDocs = sessionStore.session.stashDocs.filter(d => d.documentID !== doc.documentID); // remove the doc from docs
    }
    else { 
        doc.title = null // update the title
      }
  }

  const hits = computed(() => {
    let count = 0;
    sessionStore.session.stashDocs.forEach(doc => {
      // if (chunk.score >= sessionStore.session.minSimilarityScore/10) {
        count += doc.excerpts.length;
      // }
    });

    return count;
  })
  </script>

<style scoped>
.list_container {
  flex-grow: 1; /* Allow this container to expand and fill available space */
  overflow-y: auto; /* Make only this container scrollable */
}

:deep() .q-checkbox--dense .q-checkbox__bg {
    opacity: .7 !important;
  }

  /* Override q-item hover color */
  /* Dark theme */
  .body--dark .q-item.q-item--clickable:hover {
    background-color: #121212 !important; 
  }
  /* Light theme */
  .body--light .q-item.q-item--clickable:hover {
    background-color: #f5f5f5 !important; 
  }
</style>