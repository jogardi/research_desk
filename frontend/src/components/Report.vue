<template>
    <div class="bg-content-area notes-report p-p-0" style="height: 100%; width: 100%;">
        <q-toolbar class="fixed-toolbar">
          <q-toolbar-title style="font-size: 1rem;"><q-icon name="description" class="p-ml-2 p-mr-2"></q-icon>Report: {{sessionStore.session.name}}</q-toolbar-title>
            <q-space />
            
            <el-anchor class="p-mr-3"
            :container="scrollbarRef"
            direction="horizontal"
            type="default"
            :offset="0"
            :bounds="0"
            @click.prevent
            >
            <el-anchor-link v-if="!isSummaryEmpty" @click.native.prevent="scrollToSection('summary')" href="#summary" title="Summary" />
            <el-anchor-link v-if="sessionStore.session.explorer.insights != ''" @click.native.prevent="scrollToSection('insights')" href="#insights" title="Insights" />
            <el-anchor-link v-if="sessionStore.session.explorer.concepts != ''" @click.native.prevent="scrollToSection('concepts')" href="#concepts" title="Concepts" />
            <el-anchor-link v-if="modelStore.models.length > 0 && showChats" @click.native.prevent="scrollToSection('chats')" href="#chats" title="Chats" />
            <el-anchor-link @click.native.prevent="scrollToSection('context-docs')" href="#context-docs" title="Context" />
        </el-anchor>
        <!-- Sections tabs -->
        <tooltip-btn tooltip="Download as PDF" flat dense color="positive" icon="picture_as_pdf" size="md" @click="downloadPDF" :loading="pdfLoading" />
        <tooltip-btn tooltip="Share" icon="share" flat size="sm" color="positive" class="p-mr-1" Xstyle="font-size: .8rem;"></tooltip-btn>
        <q-separator vertical inset class="p-ml-3 p-mr-1" />
        <q-btn flat round dense color="primary" icon="close" v-close-popup />
        </q-toolbar>

        <!-- Sections -->
        <div ref="scrollbarRef" class="scrollable-content p-pl-4 p-mt-3">
            <!-- Summary -->
            <div id="summary" v-if="!isSummaryEmpty" class="p-mx-auto" style="width: 75%">
                <div class="subtitle text-h5">Summary</div>
                <hr />
                <div v-html="marked(sessionStore.session.explorer.summary)" style="font-size: 1rem;"></div>
            </div>
            <!-- Key Insights -->
            <div id="insights" v-if="sessionStore.session.explorer.insights != ''" class="p-mx-auto p-mt-4" style="width: 75%">
                <div class="subtitle text-h5">Insights</div>
                <hr />
                <div v-html="marked(sessionStore.session.explorer.insights)" style="font-size: 1rem;"></div>
            </div>
            <!-- Main Concepts -->
            <div id="concepts" v-if="sessionStore.session.explorer.concepts != ''" class="p-mx-auto p-mt-4" style="width: 75%">
                <div class="subtitle text-h5">Concepts</div>
                <hr />
                <div v-html="marked(sessionStore.session.explorer.concepts)" style="font-size: 1rem;"></div>
            </div>
            <!-- Chats -->
            <div v-if="modelStore.models.length > 0 && showChats" class="p-mx-auto p-mt-4" style="width: 75%">
                <div id="chats" class="subtitle text-h5">Chats</div>
                <hr />
                <div v-for="model in modelStore.models" clickable v-close-popup @click="addModel(model)">
                    <div v-if="sessionStore.session.chats[model.value] && sessionStore.session.chats[model.value].length > 0">                   
                        <div class="text-subtitle1"><span class="text-bold">Model:</span> {{model.label}}</div>
                        <div v-for="(message, index) in sessionStore.session.chats[model.value]" :key="index" 
                            class="message-content p-ml-5">
                            <div class="message-role text-bold" style="font-size: 1rem;">{{ message.role == 'user' ? 'Query' : 'AI Model Response' }}</div>
                                <div v-html="message.content? marked(message.content) : 'Sorry, I am not able to answer your query.'" style="font-size: 1rem;"></div>
                            </div>
                            <q-separator class="p-mt-3 p-mb-3" />

                    </div>
                </div>
            </div>
            <!-- Context Source Docuents -->
            <div id="context-docs" class="p-mx-auto" style="width: 75%; margin-top: 50px;">
                <div class="subtitle text-h5">Context</div>
                <hr />
                <div v-for="doc in sessionStore.session.contextDocs" :key="doc.documentID" class="chunk-text">
                    <!-- <div class="text-bold">{{doc.documentCategory}}{{doc.documentName}}</div> -->
                    <div class="text-subtitle1"><span class="text-bold" style="font-size: 1rem;">Document:</span> {{doc.documentCategory}}/{{doc.documentName}}</div>
                    <div class="text-subtitle2 text-bold" style="font-size: 1.2rem;"><span style="font-size: 1rem;">Title: </span>{{ doc.title }}</div>
                    <div v-for="excerpt in doc.excerpts" :key="excerpt[0]" class="p-ml-3 p-pb-3">
                        <div v-html="excerpt[2].text" style="font-size: 1rem;"></div>
                        <image-viewer :doc="doc" :excerpt="excerpt" />
                        <q-separator class="p-mt-3" />
                    </div>
                </div>
             </div>
            </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useQuasar } from 'quasar'
import ToastEditor from 'src/components/ToastEditor.vue';
import { useSessionStore } from 'src/stores/session-store';
import { marked } from 'marked';
import { useModelStore } from 'src/stores/model-store';
import TooltipBtn from 'src/components/TooltipBtn.vue'
import { useStore } from 'src/stores/main-store';
import ImageViewer from 'src/components/context-builder/ImageViewer.vue';

const $q = useQuasar()
const store = useStore()
const sessionStore = useSessionStore()
const modelStore = useModelStore()

const pdfLoading = ref(false)

const showChats = computed(() => {
  return modelStore.models.some(model => sessionStore.session.chats[model.value] && sessionStore.session.chats[model.value].length > 0)
})

const scrollbarRef = ref(null)

const scrollToSection = (targetElementId) => {
  const scrollbar = scrollbarRef.value
  const targetElement = document.getElementById(targetElementId)
  
  if (scrollbar && targetElement) {
    const offsetTop = targetElement.offsetTop
    scrollbar.scrollTop = offsetTop
  }
}

const downloadPDF = async () => {
  pdfLoading.value = true
  
  try {
    // Get the HTML content from the report
    const reportElement = scrollbarRef.value
    if (!reportElement) {
      throw new Error('Report content not found')
    }
    
    const reportData = {
      sessionName: sessionStore.session.name,
      htmlContent: reportElement.innerHTML,
      timestamp: new Date().toISOString()
    }
    
    await store.downloadPdf(reportData)
  } catch (error) {
    console.error('Error downloading PDF:', error)
  } finally {
    pdfLoading.value = false
  }
}

onMounted(() => {    
    // Set the first anchor link as active
    setTimeout(() => {
       const scrollbar = scrollbarRef.value
        if (scrollbar) {
        scrollbar.scrollTop = 5
        }
    }, 100)
})

const isSummaryEmpty = computed(() => {
    const noSummary = "There is no context text provided to summarize. Please provide the necessary text, and I'll be happy to assist you with a summary."
    return sessionStore.session.explorer.summary == '' || sessionStore.session.explorer.summary == noSummary
})
</script>

<style scoped>
.fixed-toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white; /* or match your theme */
}

.scrollable-content {
  height: calc(100% - 85px); /* Adjust based on toolbar height */
  overflow-y: auto;
}

:deep() h6 {
    margin: 0px !important;
}


  :deep() .message-content h1, :deep() .message-content h2, :deep() .message-content h3, :deep() .message-content h4, :deep() .message-content h5, :deep() .message-content h6 {
    margin-bottom: 15px !important;
    margin-top: 15px !important;
    /* color: #77bee7 !important; */
  }

  :deep() .message-content h1 {
      font-size: 1.75rem !important;
      line-height: 1.9rem !important;
  }

  :deep() .message-content h2 {
      font-size: 1.5rem !important;
      line-height: 1.6rem !important;
  }

  :deep() .message-content h3 {
      font-size: 1rem !important;
      line-height: 1.1rem !important;
  }

  :deep() .message-content h4 {
      font-size: .9rem !important;
      line-height: 1rem !important;
  }

  :deep() .message-content h5 {
      font-size: .8rem !important;
      line-height: .9rem !important;
  }

  :deep() .message-content h6 {
      font-size: .7rem !important;
      line-height: .8rem !important;
  }

  hr {
    opacity: 0.5;
  }




</style>