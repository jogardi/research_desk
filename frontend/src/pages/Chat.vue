<template>
  <div>
    <el-container id="chat" v-if="store.initialized" style="height: 100vh"  class="p-pt-2 Xp-px-3">
      <el-header height="auto">
      <div class="p-d-flex p-justify-between p-align-items-center">
        <div class="p-d-flex p-justify-start p-align-items-center text-subtitle1">
          <!-- Conversation Model dropdown list and delete button -->
          <q-select v-model="sessionStore.session.model" @update:model-value="onModelChanged"
              filled dense color="primary" label="AI Model"
              :options="modelStore.models" 
          >
            <template v-slot:option="scope">
              <!-- <div class="p-px-3 p-py-2">{{ scope.label }}</div> -->
                <q-item v-bind="scope.itemProps">
                <q-item-section>
                  <div class="p-d-flex p-align-items-center">
                    <q-item-label class="p-mr-2">{{ scope.label }}</q-item-label>
                    <q-icon v-if="sessionStore.session.chats && sessionStore.session.chats[scope.opt.value] && sessionStore.session.chats[scope.opt.value].length > 0" size="xs" color="positive" name="chat"></q-icon>
                    <!-- <q-badge v-if="sessionStore.session.chats && sessionStore.session.chats[scope.opt.value] && sessionStore.session.chats[scope.opt.value].length > 0" 
                        color="positive" text-color="white" class="p-ml-1">
                      {{ sessionStore.session.chats[scope.opt.value].length/2 }}
                    </q-badge> -->
                  </div>
                </q-item-section>
                <!-- <q-item-section avatar>
                  <q-icon  v-if="sessionStore.session.chats[scope.opt.value].length > 0" size="xs" color="positive" name="chat"></q-icon>
                </q-item-section> -->
              </q-item>
            </template>
          </q-select>
          <q-btn class="p-ml-2" icon="help_outline" dense flat color="info" size="sm">
              <q-popup-proxy Xoffset="[0, 18]">
                <div class="model-description q-pa-md">
                  <div class="text-subtitle1">Model Description</div>
                  <q-separator spaced class="bg-grey-5"/>
                  <div style="max-width: 250px;">
                    {{ sessionStore.session.model.desc}}
                  </div>
                </div>
              </q-popup-proxy>
          </q-btn>
          <tooltip-btn v-if="sessionStore.session.chats[sessionStore.session.model.value].length > 0" @click="removeConversation()" Xclass="p-ml-1"
            tooltip="Remove conversation with this model" flat dense Xround size="sm"
            icon="delete" color="primary">
          </tooltip-btn>
        </div>
          <tooltip-btn tooltip="Toggle Right Sidebar" @click="rightDrawerOpen = !rightDrawerOpen" 
              dense size="sm" flat color="primary" icon="menu"></tooltip-btn>
      </div>
      <q-separator spaced />
    </el-header>
    
    <el-main class="p-pt-0 p-pb-2">
      <!-- Conversation messages -->
      <div id="message-area" class="transparent-scrollbar message-area" style="height: 100%; overflow-y: scroll; font-size: .9rem;">
        <q-list Xbordered Xseparator style="height: 100%;">
          <q-item v-for="(message, index) in messages" :key="index" clickable class="p-pt-2 p-pb-0 p-px-2">
            <q-item-section avatar top>
                <q-icon :name="message.role == 'user' ? 'person' : 'android'" :class="message.role == 'user' ? 'person-icon' : 'android-icon'" style="opacity: .8" />
            </q-item-section>
            <q-item-section top>
              <div class="message-content">
                  <div Xstyle="font-size: .9rem" class="text-subtitle1"
                    v-html="message.content? compiledMarkdown(message.content) : 'Sorry, I am not able to answer your query.'">
                  </div>           
            </div>
              <!-- <q-separator v-if="message.role != 'user'" spaced /> -->
            </q-item-section>
            <q-item-section side top>
              <div>
              <q-btn @click="copyToClipboard(message.content, message.role)" icon="assignment" size="sm" 
                  dense flat>
              </q-btn>  
              <q-btn v-if="message.role == 'user'" @click="removeMessagePair(index)" icon="delete" size="sm" dense flat class="bg-transparent Xtext-red-3" color="primary">
                <tooltip>Remove this query and answer</tooltip>
              </q-btn>
              </div>
            </q-item-section>
          </q-item>
        </q-list>
        <!-- <q-separator v-if="messages > 0" spaced/> -->
        </div>
    </el-main>
    <el-footer :height="footerHeight" style="width: 100%;">
      <div v-if="needScrolling"  class="p-d-flex p-justify-center p-align-items-center">
        <q-btn @click="scrollToBottom()" icon="arrow_downward" color="primary" rounded class="p-mb-2"
          style="font-size: .6rem; opacity: .9" dense size="xs" outline></q-btn>
      </div>
      <div v-show="llmStore.queries.length > 0 || llmStore.pdfImages.length > 0 || llmStore.pdfURLs.length > 0" class="p-px-0 p-pb-2">
        <div class="subtitle text-subtitle1 Xp-mb-2">Tools</div>
        <el-scrollbar :height="toolsOpen? '210px' : '60px'" class="llm-query-area p-p-2" style="border-radius: 10px; position: relative;">
          <div style="position: absolute; top: 5px; right: 5px; z-index: 1000;">
            <q-btn @click="toolsOpen = !toolsOpen;" :icon="toolsOpen? 'keyboard_arrow_up' : 'keyboard_arrow_down'" 
              color="primary" flat dense no-caps size="md"/>
          </div>
          <div v-for="query in llmStore.queries" :key="query" class="p-mt-2">
            <span class="text-info">Searching Knowledgebase: </span> {{ query }}
            <q-btn icon="search" @click="gotoSemanticSearch(query)" dense size="md" flat  color="primary" />
          </div>
          <div v-for="pdfImage in llmStore.pdfImages" :key="pdfImage.document_path" class="p-mt-2">
            <span class="text-info">Reading Page: </span> 
            <span style="cursor: pointer">{{ pdfImage.document_path }} 
              <q-icon name="visibility" @click="showPdfViewer(pdfImage)" size="xs" color="primary" />
            </span>
          </div>
          <div v-for="pdfURL in llmStore.pdfURLs" :key="pdfURL.pdf_url" class="p-mt-2">
            <span class="text-info">Importing PDF from URL: </span> 
            <a :href="pdfURL.pdf_url" target="_blank">{{ pdfURL.pdf_url }}</a>
          </div>
        </el-scrollbar>
      </div>
      <!-- <div class="bg-grey-7" Xstyle="height: 100px"> -->
      <!-- User input -->
      <div class="p-px-0 Xbg-red-8" Xstyle="height: 150px;">
          <chat-query-input ref="queryInputRef" @submit="submitUserQuery" />
      </div>

        <!-- <div v-if="sessionStore.session.systemPrompt == null || sessionStore.session.systemPrompt == ''" 
          class="text-subtitle1 text-red p-pb-2" Xstyle="height: 100px">
          <q-icon name="warning" size="sm" />
          <span>You must enter the instructions to the AI model before you can input user query.</span> 
        </div> -->
      <!-- </div> -->
      </el-footer>

      <!-- pdf viewer -->
      <q-dialog v-model="store.pdfViewerData.show" position="right" full-height seamless Xpersistent>
        <div style="min-width: 750px;">
        <pdf-viewer />
        </div>
      </q-dialog>
    </el-container>

    <q-drawer id="right-drawer" v-if="store.initialized"  side="right" Xdark bordered class="q-pa-md"
        v-model="rightDrawerOpen"
        show-if-above
        :width="store.pdfViewerData.show ? 750 : 375"
      >
        <div class="subtitle text-subtitle1 q-mr-md">AI Model Data Source</div>
        <div class="row">
          <div v-if="sessionStore.session.chats[sessionStore.session.model.value] && sessionStore.session.chats[sessionStore.session.model.value].length == 0" class="row justify-end items-center" style="margin-bottom: -15px;">
              <q-toggle
                  :label="sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value]"
                  color="primary"
                  false-value="Exclude"
                  true-value="Include"
                  checked-icon="check"
                  unchecked-icon="clear"
                  v-model="sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value]"
                  @update:model-value="onExcludeInclueChanged"
                  size="sm"
                  />
              <span style="padding-left: 5px; opacity: .7"> LLM Training Data</span>
            </div>
            <div v-else>LLM Training Data is {{ sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value] }}d</div>
            <q-btn class="Xq-ml-xs" icon="help_outline" flat color="info" size="sm" round>
              <q-popup-proxy Xoffset="[0, 18]">
                <div class="model-description q-pa-md">
                  <div class="text-subtitle1">Include/Exclude LLM Training Data</div>
                  <q-separator spaced class="bg-grey-5"/>
                  <div style="max-width: 250px;">
                  <p>This setting applies to all AI Model responses for the selected AI model.</p>
                  <p><q-icon name="warning" size="sm" color="warning" /> <b>IMPORTANT: </b>You can only set this parameter once, before you start the conversation with the selected AI model.</p>
                  <p><q-icon name="info" size="sm" color="info" /> When this setting is set to "Exclude", the "Import PDFs from hyperlink (URL)" tool is disabled!</p>
                  </div>
                </div>
              </q-popup-proxy>
            </q-btn>
        </div>

        <!-- <q-separator spaced class="p-mt-2"/> -->

      <total-tokens class="p-mt-4"/>

      <!-- <div class="title Xtext-h6 q-mb-md">Chat Setup</div> -->

      <!-- <div class="row q-gutter-xl"> -->
        <!-- The system prompt -->
        <div id="sys-prompts" class="p-mt-4 q-mb-lg">

          <div class="flex justify-between items-center text-subtitle2 p=mb-4">
            <div>
            <span class="subtitle text-subtitle1">AI Model Role</span>
            <q-btn class="p-ml-1" icon="help_outline" dense flat round color="info" size="sm">
              <q-popup-proxy Xoffset="[0, 18]">
                <div class="model-description q-pa-md">
                  <div class="text-subtitle1">AI Model Role</div>
                  <q-separator spaced class="bg-grey-5"/>
                  <div style="max-width: 250px;">
                    <p>This feature allows you to instruct the AI Model to take on a specific role. The AI model will use this role to guide its responses.</p>
                    <p>This instructions apply to all AI Models and all thought flows.</p>
                    <p>You can manage AI model roles by clicking the <b>cog icon</b> on the right.</p>
                    <p><q-icon name="info" size="sm" color="info" /> You can provide other special instructions. Be as clear and concise as possible in order to get the best results.</p>
                  </div>
                </div>
              </q-popup-proxy>
          </q-btn>
        </div>
            <tooltip-btn tooltip="Manage AI Model Roles" icon="settings" @click="showLlmRoleDlg = true" :disable="!sessionStore.session.model.useRoles"
              flat color="primary" size="sm" round />

          </div>
          <!-- <q-separator spaced/> -->
          <div class="Xbg-grey-8 Xq-pa-sm Xtext-teal-3 cursor-pointer">
            <div>
              {{ selectedLlmRole}}
            </div>
          </div>
          <!-- <q-separator spaced/> -->
        </div>

        <!-- Temperature -->
        <div>
          <div class="subtitle text-subtitle1" style="margin-bottom: -45px;">Temperature</div>
          <div class="q-mb-lg" style="width: 90%">
            <q-slider
                class="q-mt-xl q-ml-sm"
                v-model="sessionStore.session.temperature"
                color="primary"
                markers
                :marker-labels="markerLabel"
                :min="0"
                :max="10"
                :step="1"
              />
          </div>
        </div>
        <div class="q-mt-md">
          <div class="text-subtitle1">Max Tokens</div>
          <div>
            <q-input Xdark dense
              type="number"
              color="primary"
              filled
              v-model="sessionStore.session.maxTokens"
              clearable
              label="Enter Max Tokens value"
              style="width: 50%" />
          </div>
        </div>
        <!-- <div class="q-mt-lg">
          <div class="text-subtitle1">Chat with Document -- Not Implemented</div>
          <q-select v-model="selectedDocument" :options="documents" @clear="onDocumentsClear" filled clearable dense 
            Xlabel="Select document to convers with" />
        </div> -->

        <div class="q-mt-lg">
          <div class="p-d-flex Xp-justify-between p-align-items-center p-mb-2">
            <div class="subtitle text-subtitle1">Use Tools</div>
            <q-btn class="Xq-ml-xs" icon="help_outline" flat color="info" size="sm" round>
              <q-popup-proxy Xoffset="[0, 18]">
                <div class="model-description q-pa-md">
                  <div class="text-subtitle1">Use Tools</div>
                  <q-separator spaced class="bg-grey-5"/>
                  <div style="max-width: 350px;">
                  <p>The AI Model can decide to use the following tools to gather more context for your query:</p>
                  <ul>
                    <li>Search Knowledgebase</li>
                    <li>Load entire page - when "Search Knowledgebase" tool is selected</li>
                    <li>Import PDFs from hyperlink(URL) - when LLM Training Data is Included</li>
                  </ul>
                  <p class="p-d-flex p-align-top">
                    <q-icon name="info" size="xs" color="info"  class="p-mr-1"/> 
                    <span>This is an <b>agentic</b> feature - the AI Model can decide to use the tools or not.</span>
                  </p>
                  </div>
                </div>
              </q-popup-proxy>
            </q-btn>
            <div v-if="sessionStore.session.model.useTools" class="p-ml-6">
              <q-btn v-show="showAllTools" @click="toggleTools(true)" label="All" icon="check" color="positive" flat dense no-caps size="sm" class="p-mr-2"/>
              <q-btn v-show="showNoneTools" @click="toggleTools(false)" label="None" icon="close" color="negative" flat dense no-caps size="sm" class="p-mr-2"/>
            </div>
          </div>
          <q-separator />
          <div v-if="sessionStore.session.model.useTools">
            <div class="p-mt-2">
            <q-checkbox v-model="sessionStore.session.useTools.searchSemanticByDoc" label="Search Knowledgebase" 
              @click="semanticSeaerchToolClick()" color="primary" size="sm" dense />
            </div>
            <div class="p-mt-2 p-ml-4">
              <q-checkbox v-model="sessionStore.session.useTools.readPage" label="Load entire page" 
              color="primary"  size="sm" dense :disable="!sessionStore.session.useTools.searchSemanticByDoc">
                <tooltip v-if="!sessionStore.session.useTools.searchSemanticByDoc">
                  <span Xclass="text-positive">
                    Enabled when "Search Knowledgebase" tool is selected.
                  </span>
                </tooltip>
              </q-checkbox> 
            </div>
            <div class="p-mt-2">
              <q-checkbox v-model="sessionStore.session.useTools.loadPdf" label="Import PDFs from hyperlink (URL)"
              :disable="sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value] == 'Exclude'"
              color="primary" size="sm" dense>
                <tooltip v-if="sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value] == 'Exclude'">
                  <span class="text-red-8">
                   Disabled when LLM Training Data is Excluded.
                  </span>
                </tooltip>
              </q-checkbox>    
            </div>
          </div>
          <div v-else class="p-mt-2">
            Tools are not supported by this model.
          </div>
        </div>
      </q-drawer>

      <LLMRoleDlg v-model="showLlmRoleDlg" />
    
    </div>
</template>

<script setup>
  import { ref, nextTick, computed, onUnmounted, onMounted, watch } from 'vue';
  import { useStore } from 'src/stores/main-store';
  import { useSessionStore } from 'src/stores/session-store';
  import { useLlmStore } from 'src/stores/llm-store';
  import { useModelStore } from 'src/stores/model-store';
  import { useSearchStore } from 'src/stores/search-store';
  import uuid4 from 'uuid4'
  import SelectedCategories from 'src/components/SelectedCategories.vue'
  import ChatQueryInput from 'src/components/ChatQueryInput.vue'
  import TooltipBtn from 'src/components/TooltipBtn.vue'
  import Tooltip from 'src/components/Tooltip.vue'
  import { marked } from 'marked';
  import useUtils from 'src/composables/useUtils';
  import TotalTokens from 'src/components/TotalTokens.vue'
  import PdfViewer from 'src/components/context-builder/PdfViewer.vue';
  import useNotify from 'src/composables/useNotify';
  import { useQuasar } from 'quasar'
  import { initializeTableSorting, removeEventListeners } from 'src/utils/tableSorter.js';
  import LLMRoleDlg from 'src/components/chat/LLMRoleDlg.vue'
  import { useRouter } from 'vue-router'
  import * as API from 'src/api/api.js';

  const router = useRouter()

  const $q = useQuasar()

  const store = useStore()
  const sessionStore = useSessionStore();
  const llmStore = useLlmStore()
  const modelStore = useModelStore()
  const searchStore = useSearchStore()
  const utils = useUtils()

  const rightDrawerOpen = ref(false)
  const toolsOpen = ref(false)

  const popup = ref(false)
  const showLlmRoleDlg = ref(false)

  const queryInputRef = ref(null) // the query input component

  const documents = [
    {label: 'None'},
  ]

  const selectedDocument = ref(documents[0])

  // composables
  const { notify, notifyProgress } = useNotify();

  const needScrolling = ref(false)

  const footerHeight = computed(() => {
    let height = 145
    if(llmStore.queries.length > 0 || llmStore.pdfImages.length > 0 || llmStore.pdfURLs.length > 0) {
      height = 245
      if (toolsOpen.value) {
        height += 150
      }
    }
    if(needScrolling.value) {
      height += 30
    }
    return height + 'px'
  })

  function checkScrollPosition() {
    const messageArea = document.getElementById('message-area')
    if (!messageArea) {
      needScrolling.value = false
      return
    }
    
    // Check if we're not at the bottom (with a 20px tolerance)
    const isAtBottom = messageArea.scrollTop + messageArea.clientHeight >= messageArea.scrollHeight - 20
    needScrolling.value = !isAtBottom
  }

  // Define messages computed property first
  const messages = computed(() => {
    if (!sessionStore.session) {
      return []
    }
    const selectedModel = sessionStore.session.model 
    if (!sessionStore.session.chats[selectedModel.value]) { // if no conversation for this model yet
      sessionStore.session.chats[selectedModel.value] = []; // initialize the conversation for this model
    }
    nextTick(() => {
      scrollToBottom();
    });
    return sessionStore.session.chats[selectedModel.value]
  })

  // Now we can watch messages
  onMounted(() => {
    if (!sessionStore.session.model.useTools) {
        toggleTools(false);
    }
    nextTick(() => {
      initializeTableSorting();
  
      // llmStore.queries = [];
      // llmStore.pdfImages = [];
      // llmStore.pdfURLs = [];
    });
  });

  // Watch for store.initialized to become true
  watch(
    () => store.initialized,
    (initialized) => {
      if (initialized) {
        nextTick(() => {
          const messageArea = document.getElementById('message-area');
          if (messageArea) {
            messageArea.addEventListener('scroll', checkScrollPosition);
            window.addEventListener('resize', checkScrollPosition);
            messageArea.addEventListener('click', handleCitationClick);
          }
        });
      }
    },
    { immediate: true }
  );

  onUnmounted(() => {
    store.pdfViewerData.show = false
    removeEventListeners();

    const messageArea = document.getElementById('message-area')
    if (messageArea) {
      messageArea.removeEventListener('scroll', checkScrollPosition)
      window.removeEventListener('resize', checkScrollPosition)
      
      // Remove event listener for citation clicks
      messageArea.removeEventListener('click', handleCitationClick);
    }
  })

  // Check scroll position whenever messages change
  watch(() => messages, () => {
    nextTick(() => {
      checkScrollPosition()
    })
  }, { deep: true })

  function onDocumentsClear() {
    selectedDocument.value = documents[0]
  }

  function toggleTools(value) {
      sessionStore.session.useTools.searchSemanticByDoc = value
      sessionStore.session.useTools.readPage = value
      sessionStore.session.useTools.loadPdf = value
  }

  const showAllTools = computed(() => {
    return !sessionStore.session.useTools.searchSemanticByDoc || !sessionStore.session.useTools.readPage || !sessionStore.session.useTools.loadPdf
  })
  const showNoneTools = computed(() => {
    return sessionStore.session.useTools.searchSemanticByDoc || sessionStore.session.useTools.readPage || sessionStore.session.useTools.loadPdf
  })

  async function submitUserQuery(userQuery) { 
    store.chatDismiss = notifyProgress('"' + sessionStore.session.model.label + '" Generating Model Response ...')
    store.chatLoading = true

    const query = userQuery 
    queryInputRef.value.clearQuery() 
    const isError = await llmStore.chat(query);
    store.chatDismiss()
    store.chatLoading = false
    if (!isError) {
      // queryInputRef.value.clearQuery()
    
      nextTick(() => {
        scrollToBottom();
      });
      nextTick(async () => {
        // queryInputRef.value.focus()
        await utils.updateTotalTokens();
      })
      nextTick(() => {
        removeEventListeners();
        initializeTableSorting();
      });
    }
  }

  function removeMessagePair(index) {
    const selectedModel = sessionStore.session.model
    const messages = sessionStore.session.chats[selectedModel.value]
    messages.splice(index, 2)
    if (messages.length == 0) {
      llmStore.queries = [];
      llmStore.pdfImages = [];
      llmStore.pdfURLs = [];
    }
    nextTick(async () => {
        await utils.updateTotalTokens();
      })
  }

  function markerLabel (val) {
    return (val/10).toFixed(1)
  }

  function removeConversation() {
    const selectedModel = sessionStore.session.model
    $q.dialog({
        title: 'Remove this conversation?',
        message: 'The conversation for this model will be removed from your thought flow.',
        cancel: true,
        ok: {
          color: 'positive'
        },
        cancel: {
          color: 'negative'
        },
        // persistent: true,
      }).onOk(async () => {
        // Add the model back to the inactive models
        // modelStore.models.find(model => model.value == selectedModel.value).active = false;
        // remove the model's conversation
        delete sessionStore.session.chats[selectedModel.value];
        llmStore.queries = [];
        llmStore.pdfImages = [];
        llmStore.pdfURLs = [];

        nextTick(async () => {
        // queryInputRef.value.focus()
        await utils.updateTotalTokens();
      })
      })
  }

  function compiledMarkdown(messageContent) {
    // First, compile the markdown
    let html = marked(messageContent);
    
    // Add target="_blank" to all <a> elements that don't already have it
    html = html.replace(/<a\s+(?![^>]*target=)[^>]*>/gi, (match) => {
      return match.replace('>', ' target="_blank">');
    });
    
    // Create a local citation counter and map for this message
    let citationCounter = 0;
    const citationMap = new Map();
    
    // Then, replace citation patterns [hash] with clickable links
    // Match 4-character alphanumeric hashes in square brackets
    html = html.replace(/\[([a-f0-9]{4})\]/g, (match, hash) => {
      // Check if we've seen this hash before in this message
      if (!citationMap.has(hash)) {
        // Assign a new sequential number starting from 1
        citationCounter++;
        citationMap.set(hash, citationCounter);
      }
      
      const citationNumber = citationMap.get(hash);
      return `<a href="#" class="citation-link" data-citation="${hash}" onclick="return false;">[${citationNumber}]</a>`;
    });
    
    // Process embed elements for tables/images
    // Replace <embed src="hash"> with placeholder that will be processed asynchronously
    html = html.replace(/<embed\s+src="([a-f0-9]{4})"\s*\/?>/gi, (match, hash) => {
      // Create a placeholder div with unique ID for async processing
      const embedId = `embed-${hash}-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
      
      // Schedule async processing of this embed
      nextTick(() => {
        processEmbedElement(embedId, hash);
      });
      
      return `<div id="${embedId}" class="embed-placeholder" data-hash="${hash}">
      </div>`;
    });
    
    return html;
  };

  // Process embed elements asynchronously
  async function processEmbedElement(embedId, hash) {
    try {
      const embedElement = document.getElementById(embedId);
      if (!embedElement) {
        console.warn(`Embed element ${embedId} not found in DOM`);
        return;
      }

      // Fetch excerpt content using the hash
      const result = await API.getExcerptByHash(hash);
      
      if (result.isError || !result.data) {
        embedElement.innerHTML = `<div class="embed-error">Error loading content for ${hash}</div>`;
        return;
      }

      const { chunks } = result.data;
      
      // Combine all chunk content
      let content = '';
      chunks.forEach(chunk => {
        content += chunk.text + ' ';
      });
      console.log("content", content)

      // Check for images in chunk regions
      const images = [];
      chunks.forEach(chunk => {
        if (chunk.region && chunk.region.image_url) {
          images.push(chunk.region.image_url);
        }
      });

      // Check if content contains HTML tables
      const hasTable = /<table[^>]*>.*?<\/table>/is.test(content);
      const hasImages = images.length > 0;
      
      let embedHtml = '';
      
      if (hasImages) {
        // Add images
        let imagesHtml = '<div class="embedded-images">';
        images.forEach((imageUrl, index) => {
          const imageId = `embedded-img-${embedId}-${index}`;
          imagesHtml += `<div class="embedded-image-container">
            <img src="${imageUrl}" class="embedded-image" alt="Embedded image" id="${imageId}" />
          </div>`;
        });
        imagesHtml += '</div>';
        embedHtml += imagesHtml;
      }
      
      if (hasTable) {
        // Extract and render tables
        const tableMatches = content.match(/<table[^>]*>.*?<\/table>/gis);
        if (tableMatches) {
          let tableHtml = '<div class="embedded-tables">';
          tableMatches.forEach(tableMatch => {
            tableHtml += tableMatch + '<br/><br/>';
          });
          tableHtml += '</div>';
          console.log("got table", tableHtml);
          embedHtml += tableHtml;
        }
      }
      
      if (hasImages || hasTable) {
        embedElement.innerHTML = embedHtml;
        
        // Add click handlers for images
        if (hasImages) {
          nextTick(() => {
            images.forEach((imageUrl, index) => {
              const imageId = `embedded-img-${embedId}-${index}`;
              const imageElement = document.getElementById(imageId);
              if (imageElement) {
                imageElement.addEventListener('click', () => {
                  showImagePopup(imageUrl);
                });
              }
            });
          });
        }
        
        // Initialize table sorting for any new tables
        if (hasTable) {
          nextTick(() => {
            setTimeout(() => {
              initializeTableSorting();
            }, 100);
          });
        }
      } else {
        // Display as text content if no tables or images
        embedElement.innerHTML = `<div class="embedded-content">${content}</div>`;
      }
      
    } catch (error) {
      console.error(`Error processing embed element ${embedId}:`, error);
      const embedElement = document.getElementById(embedId);
      if (embedElement) {
        embedElement.innerHTML = `<div class="embed-error">Failed to load content</div>`;
      }
    }
  }

  // Show image popup for embedded images
  function showImagePopup(imageUrl) {
    $q.dialog({
      title: 'View Image',
      html: true,
      message: `
        <div style="text-align: center; max-width: 90vw; max-height: 80vh;">
          <img src="${imageUrl}" style="max-width: 100%; max-height: 70vh; object-fit: contain;" alt="Full size image" />
        </div>
      `,
      ok: {
        flat: true,
        color: 'primary',
        label: 'Close'
      },
      style: 'max-width: 95vw; max-height: 90vh;'
    });
  }

  // Handle citation clicks
  async function handleCitationClick(event) {
    if (event.target.classList.contains('citation-link')) {
      event.preventDefault();
      const citationHash = event.target.dataset.citation;
      const citationMetadata = await utils.getCitationMetadata();
      const citation = citationMetadata[citationHash];
      
      console.log('Citation clicked:', citationHash);
      
      if (citation) {
        const doc = sessionStore.session.contextDocs.find(d => d.documentID === citation.documentID);
        
        if (doc && store.canViewDocument(doc) && citation.excerpt) {
          console.log('Showing citation from current context');
          store.showPdfViewer(citation.excerpt, doc);
          return;
        }
      }
      store.pdfViewerData.show = false
      await nextTick();
      await store.showPdfViewerByCitationHash(citationHash);
    }
  }

  function onModelChanged(value) {
    nextTick(async () => {
      // set tools to false if the model doesn't support tools
      if (!value.useTools) {
        toggleTools(false);
      }
        // queryInputRef.value.focus()
        await utils.updateTotalTokens();
        llmStore.queries = [];
        llmStore.pdfImages = [];
        llmStore.pdfURLs = [];
      })
    
      nextTick(() => {
        removeEventListeners();
        initializeTableSorting();
      });
  }

  async function copyToClipboard(text, role) {
    await navigator.clipboard.writeText(text)
    notify(role == 'user' ? 'Query copied to clipboard.' : 'Answer copied to clipboard.')
  }

  const selectedLlmRole = computed(() => {
    const llmRole = store.getSelectedLlmRole()
    const useRoles = sessionStore.session.model.useRoles
    if (!useRoles) {
      return 'AI Model Roles not supported by this model'
    }
    if (llmRole) {
      return llmRole.role
    }
    return 'AI Model Role not selected'
  })

  async function showPdfViewer(pdfImage) {
    store.pdfViewerData.show = false
    await nextTick();
    store.showPdfViewerByPath(pdfImage.document_path, pdfImage.page_number)
  }

  function semanticSeaerchToolClick() {
    if (!sessionStore.session.useTools.searchSemanticByDoc) {
      sessionStore.session.useTools.readPage = false
    }
  }

  function scrollToBottom() {
    const messageArea = document.getElementById('message-area')
    if (!messageArea) {
      return;
    }
    messageArea.scrollTop = messageArea.scrollHeight
    nextTick(() => {
      messageArea.scrollTop = messageArea.scrollHeight
    })
  }

  function gotoSemanticSearch(query) {
    searchStore.semanticSearchQuery = query;
    store.contextBuilderSelectedTab = 'semantic-search'
    store.fromChatQuery = true;
    router.push('/context-builder');
  }

  function onExcludeInclueChanged(value) {
    if (value == 'Exclude') {
      sessionStore.session.useTools.loadPdf = false
    }
  }
</script>
<!-- TODO move css to a separate file -->
<style scoped>
  :deep() .message-content {
    color: #fff;
    opacity: 0.666;
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

  /* Citation link styles */
  :deep() .citation-link {
    color: #5aaede;
    text-decoration: none;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0 2px;
    border-radius: 3px;
    margin-right: 2px;
  }

  :deep() .citation-link:hover {
    /* background-color: rgba(119, 190, 231, 0.2); */
    color: #0076b9;
    text-decoration: underline;
    font-size: 1.1rem;
  }

  :deep() .citation-link:active {
    background-color: rgba(119, 190, 231, 0.3);
  }

  /* Override q-item hover color */
  /* Dark theme */
  .body--dark .q-item.q-item--clickable:hover {
    background-color: #121212 !important; 
  }
  /* Light theme */
  .body--light .q-item.q-item--clickable:hover {
    background-color: #e0e0e0 !important; 
  }

/* Transparent scrollbar styles */

.transparent-scrollbar {
  /* For WebKit (Chrome, Safari, Edge) */
  scrollbar-width: thin; /* 'thin', 'auto', or 'none' for Firefox */
  scrollbar-color: transparent transparent; /* thumb and track color for Firefox */
}

.transparent-scrollbar::-webkit-scrollbar {
  width: 10px; /* Width of the scrollbar for WebKit */
}

.transparent-scrollbar::-webkit-scrollbar-track {
  background: transparent; /* Transparent track for WebKit */
}

.transparent-scrollbar::-webkit-scrollbar-thumb {
  background: transparent; /* Transparent thumb for WebKit */
}

.transparent-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(128, 128, 128, 0.5); /* Semi-transparent thumb on hover for WebKit */
}

/* Embed element styles */
.embed-placeholder {
  margin: 10px 0;
  padding: 8px 12px;
  border-radius: 6px;
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.loading-embed {
  color: #77bee7;
  font-style: italic;
  text-align: center;
  padding: 8px;
}

.embed-error {
  color: #ff6b6b;
  font-style: italic;
  text-align: center;
  padding: 8px;
}

.embedded-tables {
  margin: 10px 0;
}

:deep() .embedded-tables table {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  overflow: hidden;
}

:deep() .embedded-tables table th,
:deep() .embedded-tables table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

:deep() .embedded-tables table th {
  background-color: rgba(255, 255, 255, 0.1);
  font-weight: 600;
  color: #77bee7;
}

:deep() .embedded-tables table tr:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.embedded-content {
  margin: 10px 0;
  padding: 8px 12px;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.7);
}

/* Embedded images styles */
.embedded-images {
  margin: 10px 0;
}

.embedded-image-container {
  margin: 8px 0;
  text-align: center;
  background-color: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  padding: 8px;
}

.embedded-image {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.embedded-image:hover {
  transform: scale(1.02);
}

/* Support for very large images */
@media (max-width: 768px) {
  .embedded-image {
    max-width: 100%;
  }
}



</style>
