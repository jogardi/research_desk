<template>
  <el-container style="height: 100vh" id="context-builder" v-if="store.initialized" class="p-pt-2">
      <el-header height="auto">
    <!-- Tabs -->
     <div class="p-d-flex p-justify-between p-align-items-start">
    <q-toolbar class="q-pa-none" style="margin-top: -15px;">
      <q-tabs v-model="store.contextBuilderSelectedTab" no-caps @update:model-value="uncheckAll()" dense
        active-color="active-tab" active-bg-color="active-tab">
          <q-tab name="context" label="Context" />
          <q-tab name="stash" label="Stash"  />
          <q-tab name="semantic-search" label="Semantic Search"  />
          <q-tab name="text-search" label="Text Search"  />
          <!-- <q-tab name="summary" label="Summary" :disable="sessionStore.session && sessionStore.session.explorer.summary == ''"  /> -->
          <!-- <q-tab name="explore" label="Explore"  /> -->
      </q-tabs>
  </q-toolbar>
  <tooltip-btn tooltip="Toggle Right Sidebar" @click="rightDrawerOpen = !rightDrawerOpen" 
            dense size="sm" flat color="primary" icon="menu"></tooltip-btn>
  </div>
</el-header>
<el-main class="p-pt-0 p-px-3">
    <!-- <q-separator /> -->

    <!-- TAB PANELS -->
    
    <!-- Context panel -->
    <q-tab-panels v-model="store.contextBuilderSelectedTab" animated class="bg-content-area p-pt-3" style="height: 100%;">
      <q-tab-panel name="context"  Xstyle="height: 100%;">
        <context-panel  Xstyle="height: 100%;" />
    </q-tab-panel>

    <!-- Stash panel -->
    <q-tab-panel name="stash">
      <stash-panel />
    </q-tab-panel>

    <!-- Summary panel -->
    <!-- <q-tab-panel name="summary">
      <summary-panel />
    </q-tab-panel>
    <q-tab-panel name="explore">
      <explore-panel />
    </q-tab-panel> -->

    <!-- Semantic Search panel -->
    <q-tab-panel name="semantic-search">
        <semantic-search-panel />
    </q-tab-panel>

    <!-- Text Search panel -->
    <q-tab-panel name="text-search">
      <text-search-panel />
    </q-tab-panel>
  </q-tab-panels>
  <!-- </div> -->

  <!-- pdf viewer -->
  <q-dialog v-model="store.pdfViewerData.show" position="right" seamless full-height Xpersistent>
    <div style="min-width: 750px;">
    <pdf-viewer />
  </div>
  </q-dialog>
</el-main>
</el-container>

  <!-- 
    SIDE BAR
  -->
  <q-drawer id="right-drawer" v-if="store.initialized" side="right" bordered class="q-pa-md"
      v-model="rightDrawerOpen"
      show-if-above
      :width="store.pdfViewerData.show ? 750 : 350"
    >
    <!-- Total tokens -->
    <!-- <total-tokens /> -->
    
    <div v-if="store.contextBuilderSelectedTab == 'semantic-search'">
      <div class="title Xtext-h6 q-mb-md">Semantic Search Setup</div>

      <!-- Select vector DB -->
      <!-- <div class="subtitle text-subtitle1 q-mb-sm">Select Vector DB</div>
        <div class="q-gutter-sm q-mb-sm">
          <q-radio class="subtitle" v-model="sessionStore.session.vectorDB" val="hnswlib" color="primary">HnswLib</q-radio>
          <q-radio class="subtitle"  v-model="sessionStore.session.vectorDB" val="annoy" color="primary">Annoy</q-radio>
        </div> -->

        <!-- Top-K  -->
        <div class="subtitle text-subtitle1 q-mb-sm">Top Search Results (per category)</div>
        <div class="q-mb-md"> 
            <q-input Xdark dense
              type="number" Xbg-color="grey-6"
              color="primary"
              filled
              v-model="sessionStore.session.topK"
              Xclearable
              label="Enter Top-K value"
              style="width: 50%"
            />
        </div> 
        <!-- Minimum Similarity score -->
        <div class="subtitle text-subtitle1" style="margin-bottom: -45px;">Minimum Similarity Score</div>
        <div class="q-mb-lg" style="width: 90%">
          <q-slider Xdark dense marker-labels-class="text-grey-8"
              class="q-mt-xl q-ml-sm"
              v-model="sessionStore.session.minSimilarityScore"
              color="primary"
              markers
              :marker-labels="markerLabel"
              :min="0"
              :max="10"
              :step="1"
            />
        </div> 
        <q-separator spaced/>
      </div>
  </q-drawer>
</template>

<script setup>
  import { ref, onBeforeMount, nextTick, onMounted } from 'vue'
  import { useQuasar } from 'quasar'
  import { useStore } from 'src/stores/main-store';
  import { useSessionStore } from 'src/stores/session-store';
  import { useSearchStore } from 'src/stores/search-store';
  import useNotify from 'src/composables/useNotify';
  import ContextPanel from 'src/components/context-builder/ContextPanel.vue';
  import StashPanel from 'src/components/context-builder/StashPanel.vue';
  import SemanticSearchPanel from 'src/components/context-builder/SemanticSearchPanel.vue';
  import TextSearchPanel from 'src/components/context-builder/TextSearchPanel.vue';
  // import ExplorePanel from 'src/components/context-builder/ExplorePanel.vue';
  import SelectedCategories from 'src/components/SelectedCategories.vue'
  import TotalTokens from 'src/components/TotalTokens.vue'
  import PdfViewer from 'src/components/context-builder/PdfViewer.vue';
  import TooltipBtn from 'src/components/TooltipBtn.vue';
  // import { useRouter } from 'vue-router';

  const store = useStore()
  const sessionStore = useSessionStore();
  const searchStore = useSearchStore();

  const { notify, notifyProgress } = useNotify();

  // const router = useRouter();

  const $q = useQuasar()
    
  const rightDrawerOpen = ref(false) 
  const loading = ref(false)
  const chunksLoaded = ref(true)
  const all = ref(false)

  // Initialize the tab to 'context' by default
  store.contextBuilderSelectedTab = 'context'

  onMounted(async () => {
    if (sessionStore.session && sessionStore.session.contextDocs && sessionStore.session.contextDocs.length == 0) {
      store.contextBuilderSelectedTab = 'semantic-search'
    }
    if (store.fromChatQuery) {
      store.contextBuilderSelectedTab = 'semantic-search'
      store.fromChatQuery = false;
      
      // Submit the user query to perform semantic search
      if (searchStore.semanticSearchQuery && searchStore.semanticSearchQuery.trim() !== '') {
        const dismiss = notifyProgress("Semantic Searching Knowledgebase ...")
        store.semanticSearchLoading = true
        await searchStore.semanticSearch(searchStore.semanticSearchQuery);
        store.semanticSearchLoading = false
        dismiss()
      }
    }
  });

  onBeforeMount(async () => {
    console.log("*** ContextBuilder.vue - onBeforeMount ***")
  });

  function markerLabel (val) {
    return (val/10).toFixed(1)
  }

  function checkAll() {
    sessionStore.session.chunks.forEach(chunk => {
      chunk.checked = all.value
    })
  }

  function uncheckAll() {
    sessionStore.session.chunks.forEach(chunk => {
      chunk.checked = false
    })
    all.value = false
  }
</script>

<style scoped>
.q-tab-panel {
    padding: 0px !important;
}

.page-flex-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Make it fill the full viewport height */
  overflow: hidden; /* Prevent the page from scrolling */
}

</style>