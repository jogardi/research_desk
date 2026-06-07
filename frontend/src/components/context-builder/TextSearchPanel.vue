<template>
  <el-container style="height: 100%">
  <!-- <div class="q-pt-sm text-info text-caption">Perform a Google-like text keyword search on the knowledge base</div> -->
    <el-header height="auto">
    <div v-if="sessionStore.session.categories.length > 0">
       <!-- The User query -->
      <div class="row justify-between items-center">
      <text-query-input @submit="submitUserQuery" parent="text" class="p-d-flex p-flex-grow-1" />
      </div>
    </div>
    <div v-if="searchStore.textDocs.length > 0">
      <!-- Buttons Tollbar -->
      <q-bar class="toolbar p-mt-2 p-pt-0 search-tool-bar">
        <!-- All Checkbox -->
      <div v-if="searchStore.textDocs.length > 0" class="p-d-flex p-justify-between text-subtitle1">
        <div style="opacity: .8">
          <q-btn v-if="checkedCount != excerptCount" @click="checkAll(true)" no-caps dense Xsize="sm"
            label="Check All" icon="check" flat color="primary" class="text-subtitle2 p-mr-2" />
          <q-btn v-if="checkedCount > 0" @click="checkAll(false);" label="Uncheck All" icon="remove_done" 
            dense flat color="primary" no-caps />
        </div>
      </div>
            <q-space />
            <span style="font-size: .8rem; opacity: .7;" Xclass="p-mr-4">{{ hits }} hits returned</span>
            <div class="q-gutter-sm">
              <tooltip-btn @click="removeCheckedItems()" tooltip="Remove selected items" icon="delete" :disabled="checkedCount == 0" color="negative"></tooltip-btn>
              <tooltip-btn @click="stashCheckedItems()" tooltip="Stash selected items" icon="quiz" :disabled="checkedCount == 0" color="primary"></tooltip-btn>
              <tooltip-btn @click="moveToContextCheckedItems()" tooltip="Move selected items to the context tab" icon="playlist_add" :disabled="checkedCount == 0" no-caps dense color="primary"></tooltip-btn>
              <tooltip-btn @click="exploreTextSearchResults()" tooltip="Explore your text search results now" icon="explore" label="Explore" no-caps Xdense color="positive" class="p-px-2 p-ml-4"></tooltip-btn>
            </div>
      </q-bar>
      <!-- <q-separator /> -->
    </div>

      </el-header>

    <el-main class="p-pt-3">
    <!-- Document list -->
      <el-scrollbar height="100%">
        <!-- <div class="p-pb-4"> -->
      <div v-for="doc in searchStore.textDocs" :key="doc.documentID">
        <!-- Document Info -->
        <document-info :doc="doc" :updateCounts="updateCounts" />

        <!-- Excerpts List -->
        <q-list padding dense class="list_container p-py-2 p-pl-3">
          <q-item v-for="excerpt, excerptIndex in doc.excerpts" :key="excerpt[0]" dense clickable class="p-pl-3 p-py-2">
            <q-item-section side top> 
              <!-- Checkbox -->
              <div Xclass="p-mb-1">
                <q-checkbox @update:model-value="onCheckboxClicked" v-model="excerpt[2].checked" dense size="xs" color="primary" style="opacity: .7 !important;" />                  
                <!-- <image-viewer :doc="doc" :excerpt="excerpt" /> -->
              </div>
            </q-item-section>
            <q-item-section>
              <div class="p-d-flex p-justify-content-between p-align-items-center">
                  <div v-katex v-html="getExcerptText(excerpt, doc.chunks)" class="chunk-text"></div>                                
              </div> 
              <div> 
                  <image-viewer :doc="doc" :excerpt="excerpt" />  
                </div> 
            </q-item-section>                                                   
            <!-- Excerpt Menu -->
            <q-item-section side top>
              <q-btn v-if="doc.title" flat dense round icon="more_vert" color="primary" class="q-mr-sm">
                <q-menu anchor="bottom right" self="top right" class="menu-bg">
                  <q-list dense padding>
                    <menu-item  v-if="doc.title" @click="moveToContext(excerpt, doc)" icon="playlist_add" color="primary">
                      Move to Context
                    </menu-item>
                    <menu-item @click="moveToStash(excerpt, doc)" icon="quiz" color="primary">
                      Stash
                    </menu-item>
                    <menu-item @click="removeItem(excerpt, doc)" icon="delete" color="negative">                        
                      Remove
                    </menu-item>
                    <menu-item v-if="store.canViewDocument(doc)" @click="showPdfViewer(excerpt, doc)" color="primary" icon="open_in_new">
                      <!-- <a target="_blank" 
                        :href="`${Config.API_SERVER}/doc?documentId=${doc.documentID}&sentence_id=${doc.chunks[excerpt[0]].id}`" 
                        class="link-color">View Excerpt Source Page</a> -->
                        {{ doc.docType == 'PPT' ? 'View Slide' : 'View Excerpt' }}
                    </menu-item> 
                    <!-- <menu-item @click="flagDlg(chunk)" icon="flag" color="negative">                        
                      {{chunk.status == 'F'? 'Undo' : ''}} Mark for Removal
                    </menu-item>                   -->
                  </q-list>
                </q-menu>
              </q-btn>
            </q-item-section>
          </q-item>
          </q-list>
      </div>
    </el-scrollbar>
  </el-main>
  
  <!-- Flag Chunk dialog -->
  <q-dialog v-model="showFlagDlg" persistent>
    <q-card style="min-width: 450px">
        <q-card-section>
          <div class="text-h6">Mark Document for Removal</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-select v-model="flagItem.reason" label="Reason" filled :options="['Copyright', 'Inappropriate', 'Spam']" classs="q-mb-md" />
          <q-input v-model="flagItem.comment" label="Comment (required)" type="textarea" autogrow filled clearable />
        </q-card-section>
        <q-separator inset/>
        <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Cancel" color="yellow" v-close-popup />
          <q-btn label="Submit" @click="submitFlag()" :disabled="flagItem.comment == null || flagItem.comment.length == 0" lat color="negative" class="bg-grey-9" v-close-popup />
        </q-card-actions>
      </q-card>
  </q-dialog>
</el-container>
</template>

<script setup>
import { computed, ref, nextTick, onUnmounted, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import { useSearchStore } from 'src/stores/search-store';
import { useLlmStore } from 'src/stores/llm-store';
import TooltipBtn from 'src/components/TooltipBtn.vue'
import Tooltip from 'src/components/Tooltip.vue'
import MenuItem from 'src/components/MenuItem.vue'
import SourceDocInfo from 'src/components/context-builder/SourceDocInfo.vue' 
import TextQueryInput from 'src/components/context-builder/TextQueryInput.vue'
import useCheckAll from 'src/composables//useCheckAll';
import useNotify from 'src/composables/useNotify';
import useUtils from 'src/composables/useUtils';
import DocumentInfo from 'src/components/context-builder/DocumentInfo.vue'
import { marked } from 'marked';
import { getExcerptText, moveExcerpt, removeExcerpt, removeCheckedExcerpts, moveCheckedExcerpts, getDocumentsText } from 'src/utils/docUtils.js';
import { Config } from 'src/config.js';
import ImageViewer from 'src/components/context-builder/ImageViewer.vue';
import { initializeTableSorting, removeEventListeners } from 'src/utils/tableSorter.js';

const store = useStore()
const sessionStore = useSessionStore()
const searchStore = useSearchStore()
const llmStore = useLlmStore()
const utils = useUtils()

const router = useRouter()

const $q = useQuasar()

const loading = ref(false)

const showFlagDlg = ref(false)
const flagItem = ref({ reason: 'Copyright', comment: '' })
const chunkToFlag = ref(null)

const querySubmitted = ref(false)

// composables
const { checkedCount, excerptCount, onCheckboxClicked, checkAll, updateCounts } = useCheckAll('text-search');
const { notify, notifyProgress } = useNotify();

// // Computed property: filtered chunks
// const filteredChunks = computed(() => {
//   return sessionStore.session.chunks.filter(chunk => chunk.status == 'S');
// });

onUnmounted(() => {
  store.pdfViewerData.show = false
  removeEventListeners();
})

  function removeItem(excerpt, doc) {
    removeExcerpt(excerpt, doc); // remove the excerpt from the doc
    if (doc.chunks.length == 0) {
      searchStore.textDocs = searchStore.textDocs.filter(d => d.documentID !== doc.documentID); // remove the doc from docs
    }
    else{
      doc.title = null // update the title
    }
  }

  async function removeCheckedItems() {
  const removeDocsSet = removeCheckedExcerpts(searchStore.textDocs);
  // Remove documents that have no chunks left
  if (removeDocsSet.size > 0) {
    searchStore.textDocs = searchStore.textDocs.filter(doc => !removeDocsSet.has(doc.documentID));
  }
  checkAll(false);
}


  function stashCheckedItems() {
    moveCheckedExcerpts(searchStore.textDocs, sessionStore.session.stashDocs);
    removeCheckedItems();
  }

  async function moveToContextCheckedItems() {
    moveCheckedExcerpts(searchStore.textDocs, sessionStore.session.contextDocs);  
    removeCheckedItems();

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }

  // const filterByScore = computed(() => {
  //   const chunks = searchStore.textChunks.filter(chunk => chunk.score >= sessionStore.session.minSimilarityScore/10)
  //   return chunks
  // })

  const hits = computed(() => {
    let count = 0;
    searchStore.textDocs.forEach(doc => {
      // if (chunk.score >= sessionStore.session.minSimilarityScore/10) {
        count += doc.excerpts.length;
      // }
    });

    return count;
  })

  function flagDlg(chunk) {
    flagItem.value.reason = 'Copyright'
    flagItem.value.comment = ''
    if (chunk.status == 'F') {
      // TODO: implement undo flagging
      chunk.status = 'O'
    } 
    else {
      chunkToFlag.value = chunk
      showFlagDlg.value = true
    }
  }

  function submitFlag() {
    chunkToFlag.value.status = 'F'
    // TODO: implement flagging
  }

  async function submitUserQuery () {
    const dismiss = notifyProgress("Text Searching Knowledgebase ...")
    store.textSearchLoading = true
    await searchStore.textSearch(searchStore.textSearchQuery)
    dismiss()
    store.textSearchLoading = false
    querySubmitted.value = true

    // reset the explorer text search data
      store.explorerTextSearchData.docs = null
      store.explorerTextSearchData.summary = ''
      store.explorerTextSearchData.insights = ''
      store.explorerTextSearchData.concepts = ''
      store.explorerTextSearchData.querySuggestions = []
      store.explorerTextSearchData.query = ''
      store.explorerTextSearchData.answer = ''
      store.explorerTextSearchData.excludeInclude = 'Include'

    updateCounts()

    if (searchStore.textDocs.length == 0) {
      notify('No results found for your query', { icon: 'search_off', iconColor: 'negative', textColor: 'negative', })
    }
    
    // Initialize table sorting after content is loaded
    nextTick(() => {
      setTimeout(() => {
        removeEventListeners();
        initializeTableSorting();
      }, 1000);
    });
  }

  async function moveToContext(srcExcerpt, srcDoc) {
    const destDoc = moveExcerpt(srcExcerpt, srcDoc, sessionStore.session.contextDocs); // move excerpt to context
    destDoc.title = null // update the title
    if (srcDoc.chunks.length == 0) {
      searchStore.textDocs = searchStore.textDocs.filter(doc => doc.documentID !== srcDoc.documentID); // remove the srcDoc from source docs
    }
    else{
      srcDoc.title = null // update the title
    }

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }

  function moveToStash(srcExcerpt, srcDoc) {
    const destDoc = moveExcerpt(srcExcerpt, srcDoc, sessionStore.session.stashDocs); // move excerpt to context
    destDoc.title = null // update the title
    if (srcDoc.chunks.length == 0) {
      searchStore.textDocs = searchStore.textDocs.filter(doc => doc.documentID !== srcDoc.documentID); // remove the srcDoc from source docs
    }
    else{
      srcDoc.title = null // update the title
    }
  }

  async function showPdfViewer(excerpt, doc) {
    store.pdfViewerData.show = false
    await nextTick();
    store.showPdfViewer(excerpt, doc)
  }

  function exploreTextSearchResults() {
    router.replace({
      path: '/explorer',
      query: {
        source: 'text-search',
        results: searchStore.textDocs.length
      }
    })
  }

  // Use beforeRouteEnter to reinitialize sorting when the route is entered
  onMounted(() => {
    nextTick(() => {
      initializeTableSorting();
    });
  });
  
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