<template>
  <el-container style="height: 100%" Xclass="bg-content-area">
    <el-header height="auto">
    <!-- Buttons Toolbar -->
    <q-bar class="toolbar q-pt-none">
      <!-- All Checkbox -->
    <div v-if="sessionStore.session.contextDocs && sessionStore.session.contextDocs.length > 0" class="p-d-flex p-justify-between text-subtitle1">
      <div style="opacity: .8">
          <q-btn v-if="checkedCount != excerptCount" @click="checkAll(true)" no-caps dense
            label="Check All" icon="check" flat color="primary" class="p-mr-3" />
          <q-btn v-if="checkedCount > 0" @click="checkAll(false);" label="Uncheck All" icon="remove_done" 
            dense flat color="primary" no-caps Xsize="md"/>
        </div>

        <!-- <div class="p-d-flex p-align-center"> -->
          
          <!-- <tooltip-btn @click="sort()" :tooltip="sortBy == 'date' ? 'Sort By Publication Date' : 'Sort By Score'" flat dense color="primary" icon="sort" size="md" class="p-ml-2" /> -->
        <!-- </div> -->
    </div>
        <q-space />
        <span style="font-size: .8rem; opacity: .7;" class="q-mr-md">{{ hits }} excerpts</span>
        <div class="q-gutter-sm">
          <tooltip-btn @click="removeCheckedItems()" tooltip="Remove selected items" icon="delete" :disabled="checkedCount == 0" color="negative"></tooltip-btn>
          <tooltip-btn @click="stashCheckedItems()" tooltip="Stash selected items" icon="quiz" :disabled="checkedCount == 0" color="primary" ></tooltip-btn>
          <tooltip-btn @click="makeCheckedConcise()" tooltip="Make selected items text Concise" icon="short_text" :disabled="checkedCount == 0" no-caps dense color="primary"></tooltip-btn>
          <tooltip-btn @click="restoreCheckedToOriginal()" tooltip="Restore selected items to Original text" icon="subject" :disabled="checkedCount == 0" no-caps dense color="primary"></tooltip-btn>
          <tooltip-btn v-if="sessionStore.session.contextDocs && sessionStore.session.contextDocs.length > 0" @click="exploreContext()" 
              tooltip="Explore your context now" icon="explore" label="Explore" no-caps Xflat dense color="positive" class="p-px-2 p-ml-4"></tooltip-btn>
          <!-- <tooltip-btn @click="addChunk()" tooltip="Add a new item" icon="add" color="primary"></tooltip-btn> -->
        </div>
    </q-bar>
    <!-- <q-separator /> -->
    <div  v-if="sessionStore.session.contextDocs.length == 0" class="q-mt-md text-info text-subtitle1">
      <q-icon name="info_outline"  size="sm" stye="backgrund-color: transparent !important;"></q-icon> 
      Please perform semantic or text search and move excerpts to this Contaxt tab.
    </div>
    </el-header>

    <el-main class="p-pt-3">
    <!-- Document List -->
    <el-scrollbar height="100%">
      <div v-for="doc in sessionStore.session.contextDocs" :key="doc.documentID">
        <!-- Document Info -->
        <document-info :doc="doc" :key="doc.DocumentID" :updateCounts="updateCounts" />

        <!-- Excerpts List -->
        <q-list padding dense class="list_container p-py-2 p-pl-3">
          <q-item v-for="excerpt, excerptIndex in doc.excerpts" :key="excerpt[0]" dense clickable class="p-pl-3 p-py-2">
            <q-item-section side top> 
                <!-- Checkbox -->
                <div Xclass="p-mb-1">
                  <q-checkbox @update:model-value="onCheckboxClicked" v-model="excerpt[2].checked" dense size="xs" color="primary" style="opacity: .7 !important;" />
                </div>
                <!-- Edit Icon -->
                <span><q-icon v-if="excerpt[2].edited && excerpt[2].documentID != -1" size="sm" name="edit_note" color="grey-7" />
                  <tooltip>Edited text</tooltip>
                </span>
                <!-- Concise Icon -->
                <span><q-icon v-if="excerpt[2].concise" Xclass="p-ml-1" size="sm" name="short_text" color="grey-7" />
                  <tooltip>Concise text</tooltip>
                </span>
                <!-- Reviewed Icon -->
                <span @click="excerpt[2].reviewed = !excerpt[2].reviewed" Xv-if="excerpt[2].reviewed" Xclass="p-ml-1"><q-icon size="sm" name="playlist_add_check" 
                  :color="excerpt[2].reviewed ? 'info' : 'grey-7'" style="cursor: pointer"/>
                  <tooltip>{{excerpt[2].reviewed ? 'Reviewed' : 'Mark as Reviewed'}}</tooltip>
                </span>
            </q-item-section>

            <!-- Excerpt Text and popup editor -->
            <q-item-section>
                <div class="text-subtitle1 Xp-d-flex Xp-justify-content-start Xp-align-items-center" >
                  <!-- Excerpt text -->
                  
                    <span v-if="!excerpt[2].editing" v-katex class="chunk-text Xp-p-1" v-html="excerpt[2].text"></span>
                    <inplace-editor v-if="excerpt[2].editing" v-model="excerpt[2].text"
                    @update:modelValue="() => { excerpt[2].edited = true; excerpt[2].editing = false }" @cancel="() => excerpt[2].editing = false" 
                    />
                    <span>
                      <!-- Edit Icon -->
                      <!-- <span><q-icon v-if="excerpt[2].edited && excerpt[2].documentID != -1" size="xs" name="edit" color="info" />
                          <tooltip>Edited text</tooltip>
                      </span> -->
                      <!-- Concise Icon -->
                      <!-- <span><q-icon v-if="excerpt[2].concise" class="p-ml-1" size="sm" name="short_text" color="info" />
                        <tooltip>Concise text</tooltip>
                      </span> -->
                      <!-- <span v-if="excerpt[2].reviewed" class="p-ml-1"><q-icon size="sm" name="check" color="positive" style="cursor: pointer"/>
                          <tooltip>Reviewed</tooltip>
                      </span> -->
                  </span>
                </div>
                <image-viewer :doc="doc" :excerpt="excerpt" />
                <!-- <div v-if="excerptIndex != doc.excerpts.length - 1" class="p-d-flex p-justify-content-center" 
                  style="padding-top: 10px; padding-bottom: 10px; line-height: 1px; font-weight: 700; font-size: 1rem; opacity: .8">
                  . . .
                </div> -->
            </q-item-section>

            <!-- Excerpt Menu -->
            <q-item-section side top>
                <div class="p-d-flex Xjustify-end Xp-align-items Xchunk-title Xtext-subtitle1">
                  <q-btn @click="showPopup = false" icon="sticky_note_2" dense flat size="sm" 
                    :color="excerpt[2].stickyNote? 'amber-5' : 'primary' " Xclass="p-mr-0">
                  </q-btn>
                  <q-popup-proxy v-model="excerpt[2].showSticky" :offset="[270, 0]">
                      <div class="p-p-2 bg-yellow-2 text-black" style="width: 280px; height: 250px;">
                        <div class="p-d-flex p-justify-between"> 
                        <div class="text-subtitle2">Sticky Note</div>
                        <q-btn v-if="excerpt[2].stickyNote || excerpt[2].stickyNote != ''" @click="excerpt[2].stickyNote = ''"
                            flat color="negative" no-caps size="sm" icon="cancel">
                                <tooltip>Clear</tooltip>
                            </q-btn> 
                        </div>
                        <div style="border: 1px solid #ddd">
                          <textarea v-model="excerpt[2].stickyNote" class="bg-yellow-2" Xrows="10"
                            style="border: none; width: 100%; height: 200px; padding: 10px; resize: none;">
                          </textarea>
                        </div>
                      </div>
                    </q-popup-proxy>
                  <q-btn flat dense Xround size="md" icon="more_vert" color="primary" Xclass="q-mr-sm">
                    <q-menu anchor="bottom right" self="top right" class="menu-bg">
                      <q-list dense padding>
                        <menu-item v-if="excerpt[2].concise || excerpt[2].edited" @click="toggleConcise(excerpt, doc)" icon="subject" color="primary" >
                          Restore Original Text
                        </menu-item>
                        <menu-item v-if="!excerpt[2].concise" @click="toggleConcise(excerpt, doc)" icon="short_text" color="primary" >
                          Concise
                        </menu-item>  
                        <menu-item @click="excerpt[2].editing = true" icon="edit_note" color="primary">
                          Edit
                        </menu-item>
                        <menu-item @click="moveToStash(excerpt, doc)" icon="settings_backup_restore" color="primary">
                          Stash
                        </menu-item>
                        <!-- <menu-item @click="excerpt[2].reviewed = !excerpt[2].reviewed" icon="check" color="primary">
                          Toggle Reviewed
                        </menu-item> -->
                        <menu-item @click="removeItem(excerpt, doc)" icon="delete" color="negative">
                          Remove
                        </menu-item> 
                        <menu-item v-if="store.canViewDocument(doc)" @click="showPdfViewer(excerpt, doc)" color="primary" icon="open_in_new">
                          <!-- <a target="_blank" 
                            :href="`${Config.API_SERVER}/doc?documentId=${doc.documentID}&sentence_id=${doc.chunks[excerpt[0]].id}`" 
                            class="link-color">View Excerpt Source Page</a> -->
                        {{ doc.docType == 'PPT' ? 'View Slide' : 'View Excerpt' }}
                    </menu-item>                     
                      </q-list>
                  </q-menu>
                </q-btn>
              </div>
            </q-item-section>                            
          </q-item>
        </q-list>
        <!-- <q-separator v-if="filteredChunks.length > 0" Xspaced/> -->
      </div>
    </el-scrollbar>
  </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import { useLlmStore } from 'src/stores/llm-store';
import TooltipBtn from 'src/components/TooltipBtn.vue'
import useCheckAll from 'src/composables//useCheckAll';
import Tooltip from 'src/components/Tooltip.vue'
import MenuItem from 'src/components/MenuItem.vue'
import DocumentInfo from 'src/components/context-builder/DocumentInfo.vue'
import InplaceEditor from 'src/components/InplaceEditor.vue'
import { moveExcerpt, removeExcerpt, restoreChunks, removeCheckedExcerpts, moveCheckedExcerpts, getDocumentsText } from 'src/utils/docUtils.js';
import { Config } from 'src/config.js';
import ImageViewer from 'src/components/context-builder/ImageViewer.vue';
import useNotify from 'src/composables/useNotify.js';
import uuid4 from 'uuid4'
import { initializeTableSorting, removeEventListeners } from 'src/utils/tableSorter.js';

const store = useStore()
const sessionStore = useSessionStore();
const llmStore = useLlmStore()

const { notifyProgress } = useNotify()

const router = useRouter()

const stickyEditor = ref(false)
const showPopup = ref(false);

const $q = useQuasar()

// const sortBy = ref('date')

// Composables
const { checkedCount, excerptCount, onCheckboxClicked, checkAll, updateCounts } = useCheckAll('context');

onUnmounted(() => {
  store.pdfViewerData.show = false
  removeEventListeners();
})

onMounted(() => {
  nextTick(() => {
    initializeTableSorting();
  });
});

async function stashCheckedItems() {
    moveCheckedExcerpts(sessionStore.session.contextDocs, sessionStore.session.stashDocs);
    removeCheckedItems();

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }
  
  async function removeCheckedItems() {
    const removeDocsSet = removeCheckedExcerpts(sessionStore.session.contextDocs);
    // Remove documents that have no chunks left
    if (removeDocsSet.size > 0) {
      sessionStore.session.contextDocs = sessionStore.session.contextDocs.filter(doc => !removeDocsSet.has(doc.documentID));
    }
    checkAll(false);

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
  }


  // const addChunk = () => {
  //   // TODO: popup a dialog to allow addding a new chunk
  //   const id = uuid4()
  //   sessionStore.session.chunks.unshift({ // add to the beginning of the array
  //     id: id,
  //     text: 'Click the round pencil icon to edit',
  //     status: 'O',
  //     checked: false,
  //     score: 1.0,
  //     title: 'Manually Added',
  //     documentID: -1, // no source document - manually added
  //   })
  // }

  async function makeCheckedConcise() {
    const dismiss = notifyProgress('Generating Concise Text ...');

    const excerpts = [];
    
    // Collect excerpts that need to be concised
    for (const doc of sessionStore.session.contextDocs) {
        for (const excerpt of doc.excerpts) {
            if (excerpt[2].checked && !excerpt[2].concise) {
                excerpts.push(excerpt);
            }
        }
    }

    //Process all excerpts in parallel
    const promises = excerpts.map(async (excerpt) => {
        excerpt[2].text = await llmStore.getExcerptConcise(excerpt[2].text);
        excerpt[2].concise = true;
    });

    // Wait for all async operations to complete
    await Promise.all(promises);

    // Processing as finished
    dismiss()
    checkAll(false);
}

async function restoreCheckedToOriginal() {
  const dismiss = notifyProgress('Restoring Original Text ...')

    const excerpts = [];
    const docs = {};
    // Collect excerpts that need to be concised
    for (const doc of sessionStore.session.contextDocs) {
        for (const excerpt of doc.excerpts) {
            if (excerpt[2].checked && (excerpt[2].concise || excerpt[2].edited)) {
                excerpts.push(excerpt);
                docs[doc.documentID] = doc;
            }
        }
    }

    //Process all excerpts in parallel
    const promises = excerpts.map(async (excerpt) => {
      const doc = docs[excerpt[2].documentID];
      const firstChunkId = doc.chunks[excerpt[0]].id; 
      const lastChunkId = doc.chunks[excerpt[1]].id;
      const originalChunks = await llmStore.restoreOriginal(excerpt[2].documentID, firstChunkId, lastChunkId);
      restoreChunks(excerpt, originalChunks, doc);
      excerpt[2].edited = false
      excerpt[2].concise = false
    });

    // Wait for all async operations to complete
    await Promise.all(promises);

    // Processing as finished
    dismiss()
    checkAll(false);
}

  const hits = computed(() => {
    let count = 0;
    sessionStore.session.contextDocs.forEach(doc => {
      // if (chunk.score >= sessionStore.session.minSimilarityScore/10) {
        count += doc.excerpts.length;
      // }
    });

    return count;
  })

  // Computed property: filtered chunks
  const filteredChunks = computed(() => {
      return sessionStore.session.chunks.filter(chunk => chunk.status !== 'S');
  });


  /**
   * Context Item Methods
   */
   async function moveToStash(srcExcerpt, doc) {
    const destDoc = moveExcerpt(srcExcerpt, doc, sessionStore.session.stashDocs); // move excerpt to context
    destDoc.title = null // update the title
    if (doc.chunks.length == 0) {
      sessionStore.session.contextDocs = sessionStore.session.contextDocs.filter(d => d.documentID !== doc.documentID); // remove the srcDoc from source docs
    }
    else {
        doc.title = null // update the title
    }

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
}

async function removeItem(excerpt, doc) {
    removeExcerpt(excerpt, doc); // remove the excerpt from the doc
    if (doc.chunks.length == 0) {
      sessionStore.session.contextDocs = sessionStore.session.contextDocs.filter(d => d.documentID !== doc.documentID); // remove the doc from docs
    }
    else {
        doc.title = null // update the title
    }

    const contextText = getDocumentsText(sessionStore.session.contextDocs);
    await llmStore.generateSuggestedQueries(contextText)
}


async function  restoreOriginal(excerpt, doc) {
  const dismiss = notifyProgress('Restoring Original Text ...')
  const firstChunkId = doc.chunks[excerpt[0]].id; 
  const lastChunkId = doc.chunks[excerpt[1]].id;
  const originalChunks = await llmStore.restoreOriginal(excerpt[2].documentID, firstChunkId, lastChunkId);
  restoreChunks(excerpt, originalChunks, doc)
  excerpt[2].edited = false
  excerpt[2].concise = false
  dismiss()
}

async function toggleConcise(excerpt, doc) {
      const dismiss = notifyProgress('Generating Concise Text ...')
      if (!excerpt[2].concise) {
        excerpt[2].text = await llmStore.getExcerptConcise(excerpt[2].text)
        excerpt[2].concise = true
      }
      else {
        await restoreOriginal(excerpt, doc)
      }
      dismiss()
}

async function showPdfViewer(excerpt, doc) {
  store.pdfViewerData.show = false
  await nextTick();
  store.showPdfViewer(excerpt, doc)
}

function exploreContext() {
  router.replace({
    path: '/explorer',
    query: { source: 'context', results: sessionStore.session.contextDocs.length }
  })
}

// function sort() {
//     if (sortBy.value == 'date') {
//       sortBy.value = 'score'
//       sessionStore.session.contextDocs.sort((a, b) => {
//         return new Date(b.publicationDate) - new Date(a.publicationDate);
//       });
//     }
//     else {
//       sortBy.value = 'date'
//       sessionStore.session.contextDocs.sort((a, b) => {
//         return b.score - a.score;
//       });
//     }
//   }
</script>

<style scoped>
.list_container {
  flex-grow: 1; /* Allow this container to expand and fill available space */
  overflow-y: auto; /* Make only this container scrollable */
}

.document-info .text-subtitle1 {
    font-size: 1.1rem !important;
    cursor: pointer;
  }


  textarea:focus {
    outline: none !important;
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