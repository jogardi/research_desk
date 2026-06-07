<template>
  <el-container style="height: 100%">
  <!-- <div class="q-pt-sm text-info text-caption">Perform meaning-based search on the knowledge base</div> -->
  <el-header height="auto">
    <!-- The User query -->
    <div v-if="sessionStore.session.categories.length > 0">
      <div class="row justify-between items-center">
      <semantic-query-input @submit="submitUserQuery" class="p-d-flex p-flex-grow-1" />
      </div>
    </div>

    <div v-if="searchStore.semanticDocs.length > 0">
      <!-- Buttons Tollbar -->
      <q-bar class="toolbar p-mt-2 p-pt-0 search-tool-bar">
        <!-- All Checkbox -->
       <div v-if="searchStore.semanticDocs.length > 0" class="p-d-flex p-justify-between text-subtitle1">
        <div style="opacity: .8">
          <q-btn v-if="checkedCount != excerptCount" @click="checkAll(true)" no-caps dense Xsize="sm"
            label="Check All" icon="check" flat color="primary" class="p-mr-3" />
          <q-btn v-if="checkedCount > 0" @click="checkAll(false);" label="Uncheck All" icon="remove_done" 
            dense flat color="primary" no-caps />
        </div>
      </div>
            <q-space />
            <div class="p-d-flex p-align-center">
          <span style="font-size: .8rem; opacity: .7;" Xclass="p-mr-4">{{ hits }} hits returned</span>
          <tooltip-btn @click="sort()" :tooltip="sortBy == 'date' ? 'Sort By Publication Date' : 'Sort By Score'" flat dense color="primary" icon="sort" size="md" class="p-ml-2" />
        </div>
            <div class="q-gutter-sm">
              <tooltip-btn @click="removeCheckedItems()" tooltip="Remove selected items" icon="delete" :disabled="checkedCount == 0" color="negative"></tooltip-btn>
              <tooltip-btn @click="stashCheckedItems()" tooltip="Stash selected items" icon="quiz" :disabled="checkedCount == 0" color="primary"></tooltip-btn>
              <tooltip-btn @click="moveToContextCheckedItems()" tooltip="Move selected items to the context tab" icon="playlist_add" :disabled="checkedCount == 0" no-caps dense color="primary"></tooltip-btn>
              <tooltip-btn @click="exploreSemanticSearchResults()" tooltip="Explore your semantic search results now" icon="explore" label="Explore" no-caps dense color="positive" class="p-px-2 p-ml-4"></tooltip-btn>
            </div>
      </q-bar>
      <!-- <q-separator /> -->
    </div>

    </el-header>

    <el-main>
    <!-- Document list -->
    <el-scrollbar Xalways height="100%">
      <div v-for="doc in searchStore.semanticDocs" :key="doc.documentID">
        <div v-if="doc.score && doc.score >= sessionStore.session.minSimilarityScore/10" :doc="doc">
        <!-- Document Info -->
        <document-info :doc="doc" :updateCounts="updateCounts" />

        <!-- Excerpts List -->
        <q-list padding dense class="list_container p-py-2 p-pl-3">
          <q-item  v-for="excerpt, excerptIndex in doc.excerpts" :key="excerpt[0]" dense clickable 
              class="p-pl-3 p-py-2" Xstyle="`${excerpt[2].score && excerpt[2].score < sessionStore.session.minSimilarityScore/10? 'display: none;' : ''}`">
            <q-item-section side top> 
              <!-- Checkbox -->
              <div Xclass="p-d-flex p-mb-1">
                <q-checkbox @update:model-value="onCheckboxClicked" v-model="excerpt[2].checked" dense size="xs" color="primary" style="opacity: .7 !important;"/>
              </div>
            </q-item-section>
            <q-item-section>
              <!-- <div style="opacity: .7">Score: {{ excerpt[2].score }}</div> -->
              <div Xclass="p-d-flex Xp-justify-content-between p-align-items-center">
                  <div v-katex v-html="getExcerptText(excerpt, doc.chunks)" class="chunk-text"></div>                               
              </div>  
              <image-viewer :doc="doc" :excerpt="excerpt" />
            </q-item-section>                                                   
            <!-- Excerpt Menu -->
            <q-item-section side top>
              <q-btn v-if="doc.title" flat dense round icon="more_vert" color="primary" 
                     data-testid="excerpt-menu-button" :data-excerpt-index="excerptIndex" :data-doc-id="doc.documentID">
                <q-menu anchor="bottom right" self="top right" class="menu-bg" data-testid="excerpt-menu">
                  <q-list dense padding>
                    <menu-item @click="moveToContext(excerpt, doc)" icon="playlist_add" color="primary">
                      Move to Context
                    </menu-item>
                    <menu-item @click="moveToStash(excerpt, doc)" icon="quiz" color="primary">
                      Stash
                    </menu-item>
                    <menu-item @click="removeItem(excerpt, doc)" icon="delete" color="negative">                        
                      Remove
                    </menu-item>
                    <menu-item v-if="store.canViewDocument(doc)" @click="showPdfViewer(excerpt, doc)" color="primary" icon="open_in_new"
                               data-testid="view-excerpt-source-page">
                      <!-- <a target="_blank" 
                        :href="`${Config.API_SERVER}/doc?documentId=${doc.documentID}&sentence_id=${doc.chunks[excerpt[0]].id}`" 
                        class="link-color">View Excerpt Source Page</a> -->
                        {{ doc.docType == 'PPT' ? 'View Slide' : 'View Excerpt' }}
                    </menu-item> 
                    <menu-item @click="searchExcerpt(excerpt, doc)" icon="search" color="primary">                        
                      Search for similar content 
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
import SemanticQueryInput from 'src/components/context-builder/SemanticQueryInput.vue'
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

const router = useRouter()

const utils = useUtils()

const $q = useQuasar()

const loading = ref(false)

const showFlagDlg = ref(false)
const flagItem = ref({ reason: 'Copyright', comment: '' })
const chunkToFlag = ref(null)

const querySubmitted = ref(false)

const sortBy = ref('date')

// composables
const { checkedCount, excerptCount, onCheckboxClicked, checkAll, updateCounts } = useCheckAll('semantic-search');
const { notify, notifyProgress } = useNotify();

// // Computed property: filtered chunks
// const filteredChunks = computed(() => {
//   return sessionStore.session.chunks.filter(chunk => chunk.status == 'S');
// });

onMounted(() => {
  nextTick(() => {
    initializeTableSorting();
  });
});

onUnmounted(() => {
  store.pdfViewerData.show = false
  removeEventListeners();
})

function removeItem(excerpt, doc) {
    removeExcerpt(excerpt, doc); // remove the excerpt from the doc
    if (doc.chunks.length == 0) {
      searchStore.semanticDocs = searchStore.semanticDocs.filter(d => d.documentID !== doc.documentID); // remove the doc from docs
    }
    else{
      doc.title = null // update the title
    }
}

function removeCheckedItems() {
  const removeDocsSet = removeCheckedExcerpts(searchStore.semanticDocs);
  // Remove documents that have no chunks left
  if (removeDocsSet.size > 0) {
    searchStore.semanticDocs = searchStore.semanticDocs.filter(doc => !removeDocsSet.has(doc.documentID));
  }
  checkAll(false);
}


function stashCheckedItems() {
    moveCheckedExcerpts(searchStore.semanticDocs, sessionStore.session.stashDocs);
    removeCheckedItems();
  }

  async function moveToContextCheckedItems() {
    moveCheckedExcerpts(searchStore.semanticDocs, sessionStore.session.contextDocs);  
    removeCheckedItems();
    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText);
  }

  const hits = computed(() => {
    let excerptCount = 0;
    searchStore.semanticDocs.forEach(doc => {
      if (doc.score && doc.score >= sessionStore.session.minSimilarityScore/10) {
        doc.excerpts.forEach(excerpt => {
          // if (excerpt[2].score >= sessionStore.session.minSimilarityScore/10) {
            excerptCount++
          // }
        });
      }
    });
    return excerptCount;
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
    const dismiss = notifyProgress("Semantic Searching Knowledgebase ...")
    store.semanticSearchLoading = true
    await searchStore.semanticSearch(searchStore.semanticSearchQuery)
    store.semanticSearchLoading = false
    dismiss()
    querySubmitted.value = true
    sortBy.value = 'date'
  
    // reset the explorer semantic search data
    store.explorerSemanticSearchData.docs = null
    store.explorerSemanticSearchData.summary = ''
    store.explorerSemanticSearchData.insights = ''
    store.explorerSemanticSearchData.concepts = ''
    store.explorerSemanticSearchData.querySuggestions = []
    store.explorerSemanticSearchData.query = ''
    store.explorerSemanticSearchData.answer = ''
    store.explorerSemanticSearchData.excludeInclude = 'Include'

    updateCounts()

    if (searchStore.semanticDocs.length == 0) {
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
      searchStore.semanticDocs = searchStore.semanticDocs.filter(doc => doc.documentID !== srcDoc.documentID); // remove the srcDoc from source docs
    }
    else {
      srcDoc.title = null // update the title
    }
    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }

  async function moveToStash(srcExcerpt, srcDoc) {
    const destDoc = moveExcerpt(srcExcerpt, srcDoc, sessionStore.session.stashDocs); // move excerpt to context
    destDoc.title = null // update the title
    if (srcDoc.chunks.length == 0) {
      searchStore.semanticDocs = searchStore.semanticDocs.filter(doc => doc.documentID !== srcDoc.documentID); // remove the srcDoc from source docs
    }
    else { 
        srcDoc.title = null // update the title
      }
  }

  async function showPdfViewer(excerpt, doc) {
    store.pdfViewerData.show = false
    await nextTick();
    store.showPdfViewer(excerpt, doc)
  }

  async function searchExcerpt(excerpt, doc) {
    const html = getExcerptText(excerpt, doc.chunks)
    // extract the text from the html
    const text = html.replace(/<[^>]*>?/g, '').trim()
    
    searchStore.semanticSearchQuery = text
    await submitUserQuery()
  }

  function exploreSemanticSearchResults() {
    router.replace({
      path: '/explorer',
      query: {
        source: 'semantic-search',
        results: searchStore.semanticDocs.length
      }
    })
  }

  function sort() {
    if (sortBy.value == 'date') {
      sortBy.value = 'score'
      searchStore.semanticDocs.sort((a, b) => {
        return new Date(b.publicationDate) - new Date(a.publicationDate);
      });
    }
    else {
      sortBy.value = 'date'
      searchStore.semanticDocs.sort((a, b) => {
        return b.score - a.score;
      });
    }
  }

  window.getPdfPageForFirstChunk = function() {
    // return document id and page number for the first chunk
    const doc = searchStore.semanticDocs[0]
    const excerpt = doc.excerpts[0]
    const chunk = doc.chunks[excerpt[0]]
    return { documentID: doc.documentID, pageNumber: chunk.region.page_number }
  }
</script>

<style>
  .list_container {
    flex-grow: 1; /* Allow this container to expand and fill available space */
    overflow-y: auto; /* Make only this container scrollable */
  }

  .document-info .text-subtitle1 {
    font-size: 1.1rem !important;
    cursor: pointer;
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