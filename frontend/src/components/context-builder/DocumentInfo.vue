<template>
    <div  class="p-d-flex p-justify-content-between p-align-items-center">
            <div>
              <div class="document-info">
                <span>Category: {{ doc.documentCategory}}</span>
                <q-btn @mouseenter="showCatDesc = true" icon="visibility" color="grey-6" size="xs" flat dense class="p-ml-2">
                  <q-popup-proxy v-model="showCatDesc"  @before-show="getCategoryDescription" style="width: 400px;"
                    anchor="top middle" self="top middle">
                    <div @mouseleave="showCatDesc = false">
                      <div class="p-pt-2 p-pl-2"><b>Category:</b> {{ doc.documentCategory}}</div>
                      <q-separator spaced />
                      <el-scrollbar height="300px" class="p-p-2">
                        <div v-html="marked(catDescription)"></div>
                      </el-scrollbar>
                    </div>
                  </q-popup-proxy>
                </q-btn>
              </div>
              <div class="document-info" style="cursor:auto">
                <span>Document: {{ doc.documentName  }}</span>
                <!-- <span class="p-mx-2 text-negative">{{ doc.docType }}</span> -->
                <q-icon v-if="doc.documentName.endsWith('mp4')" name="fa-solid fa-file-mp4" size="" coxslor="document-info" class="p-ml-1" />
                <q-icon v-if="doc.documentName.endsWith('mp3')" name="fa-solid fa-file-mp3" size="xs" color="document-info" class="p-ml-1" />
                <q-icon v-if="doc.docType == 'PPT'" name="fa-solid fa-file-powerpoint" size="xs" color="info" class="p-ml-1" />
                <q-icon v-if="doc.docType == 'PDF'" name="fa-solid fa-file-pdf" size="xs" color="info" class="p-ml-1" />
                <q-icon v-if="doc.docType == 'CSV'" name="fa-solid fa-file-csv" size="xs" color="info" class="p-ml-1" />
                <span class="p-ml-2" style="font-size: .75rem; opacity: .7">({{ doc.publicationDate || todayYYYYMMDD() }})</span>
                <q-btn @mouseenter="showDocDesc = true" icon="visibility" color="grey-6" size="xs" flat dense class="p-ml-2">
                  <q-popup-proxy v-model="showDocDesc"  @before-show="getDocDescription" style="width: 400px;"
                  anchor="top middle" self="top middle">
                  <div @mouseleave="showDocDesc = false">
                      <div class="p-pt-2 p-pl-2"><b>Document:</b> {{ doc.documentName}}</div>
                      <q-separator spaced />
                      <el-scrollbar height="300px" class="p-p-2">
                        <div v-html="marked(docDescription)"></div>
                      </el-scrollbar>
                    </div>
                  </q-popup-proxy>
                </q-btn>
              </div>
              <div v-if="doc.score" style="opacity: .7">Score: {{ doc.score }}</div>
              <div v-if="doc.title" class="text-h6 subtitle" style="font-size: 1.1rem;">
                <q-checkbox @update:model-value="onCheckboxClicked" v-model="doc.checked" dense size="xs" color="primary" class="p-mr-2" style="opacity: .7 !important;" />
                {{doc.title}}
              </div>
              <div v-else class="text-subtitle1 subtitle"><q-spinner-audio thickness="10" size="sm"/> Generating title ...</div>
            </div>
            <div class="p-d-flex p-pr-4 p-align-items-center">
              <!-- <tooltip-btn @click="showFlagDlg = true" tooltip="Mark document for removal" icon="flag" color="primary" flat class="p-mr-2"></tooltip-btn>               -->
              <span 
                @click="handleViewSourceDocument(doc.documentID)" 
                class="p-mr-2 underline"
                style="cursor: pointer; opacity: .8; text-decoration: underline;"
                title="View source document"
              >
              <tooltip-btn tooltip="View source document" class="p-mr-2" flat size="md" icon="description" color="info">
              </tooltip-btn>
                  
                
              </span>
            </div>
        </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useStore } from 'src/stores/main-store';
import { useSearchStore } from 'src/stores/search-store';
import { Config } from 'src/config.js';
import { useLlmStore } from 'src/stores/llm-store';
import { getDocText } from 'src/utils/docUtils.js';
import { marked } from 'marked';
import TooltipBtn from 'src/components/TooltipBtn.vue';
import useNotify from 'src/composables/useNotify.js';

const store = useStore();
const llmStore = useLlmStore();
const searchStore = useSearchStore();
const {  notifyProgress } = useNotify();

const props = defineProps({
    doc: {
        type: Object,
        required: true
    },
    updateCounts: {
        type: Function,
        required: true
    }
})

const docDescription = ref('')
const catDescription = ref('')
const showCatDesc = ref(false);
const showDocDesc = ref(false);

watch(() => props.doc.title, async (newVal) => {
  if (!props.doc.title) {
    generateTitle()
  }
})

onMounted(async () => {
  if (!props.doc.title) {
    generateTitle()
  }
})

async function generateTitle() {
  let docText = getDocText(props.doc)
  docText = docText.replace(/<b>/g, '').replace(/<\/b>/g, '')
  // Prefer the current semantic or text search query as the user's query input
  const semanticQ = searchStore.semanticSearchQuery
  const textQ = searchStore.textSearchQuery
  const queryStr = (typeof semanticQ === 'string' && semanticQ.trim().length > 0)
    ? semanticQ
    : ((typeof textQ === 'string' && textQ.trim().length > 0) ? textQ : null)
  props.doc.title = await llmStore.generateTitle(docText, queryStr)
}

async function getDocDescription() {
  if (!docDescription.value) {
    docDescription.value = await store.getDocumentDescription(props.doc.documentID)
  }
}

async function getCategoryDescription() {
  if (!catDescription.value) {
    catDescription.value = await store.getCategoryDescription(props.doc.documentCategory)
  }
}

function onCheckboxClicked(value, evt) {
  props.doc.excerpts.forEach(excerpt => {
    excerpt[2].checked = value
  });

  props.updateCounts()
}

async function handleViewSourceDocument(documentId) {
  notifyProgress('Loading source document ...', 3000);
  const result = await store.viewSourceDocument(documentId);
  
  if (!result.isError && result.data) {
    // Create a temporary URL for the blob
    const url = window.URL.createObjectURL(result.data);
    
    // Open in new tab
    window.open(url, '_blank');
    
    // Clean up the temporary URL after a short delay
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  }
  // Error handling is already done in the API layer via _notifyException
}

function todayYYYYMMDD() {
  // return the date in the format YYYY-MM-DD
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
  }
</script>