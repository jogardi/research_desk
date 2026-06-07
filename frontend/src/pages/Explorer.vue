<template>
<el-container style="height: 100vh" id="context-builder" v-if="store.initialized" class="p-pt-2">
    <el-header height="auto">
        <!-- Tabs -->
        <q-toolbar id="explorer-tabs" class="q-pa-none q-mt-sm" style="margin-top: -15px;">
                <q-tabs v-model="selectedTab" no-caps dense
                    active-color="active-tab" active-bg-color="active-tab">
                    <q-tab name="summary" label="Summary"  />
                    <q-tab name="insights" label="Insights"  />
                    <q-tab name="concepts" label="Concepts"  />
                    <q-tab name="questions" label="Query Suggestions"  />
                    <q-tab name="ask" label="Ask" />
                </q-tabs>
                <!-- <q-space /> -->
                 
                <tooltip-btn @click="copyToClipboard()" label="" class="p-ml-2" style="opacity: 0.6;"
                    icon="assignment" flat size="sm" Xcolor="primary" tooltip="Copy tab contents to clipboard">
                </tooltip-btn>
                <tooltip-btn @click="refresh()" label="" Xclass="q-ml-sm" 
                    icon="refresh" flat size="sm" color="primary" tooltip="Refresh tabs contents, except the Ask tab">
                </tooltip-btn> 
                <tooltip-btn v-if="store.currentExplorerSource != 'context'" @click="showReport = true" tooltip="Report" color="info"
                    icon="description" flat size="sm">          
                </tooltip-btn>
                </q-toolbar>
    </el-header>
    <el-main class="bg-content-area p-pt-1 p-px-3">
        <q-tab-panels v-model="selectedTab" animated class="bg-content-area p-pt-3" style="height: 100%;">
            <!-- Ask panel -->
            <q-tab-panel name="ask" style="height: 100%">
                <el-container style="height: 100%">
                <el-header height="auto">
                <q-input
                    v-model="store.explorerData.query"
                    @keydown.enter.stop="submitUserQuery"
                    color="primary"
                    outlined
                    rounded
                    dense
                    clearable
                    autogrow
                    Xtype="textarea"
                    label="Enter your query about the current context ..."
                    hint="* Your query will be submitted to the default meta-llama/Llama-4-Scout-17B-16E-Instruct AI model"
                    :disable="store.explorerLoadingAsk"
                    :loading="store.explorerLoadingAsk"
                >
                    <template v-slot:append>
                    <q-btn
                        @click="submitUserQuery"
                        class="q-ml-sm"
                        :disabled="store.explorerData.query == null || store.explorerData.query == '' || store.explorerLoadingAsk"
                        size="sm"
                        rounded
                        color="grey-10"
                        icon="arrow_upward"
                    />
                    </template>
                </q-input>
                </el-header>
                <el-main style="height: 100%">
                    <el-scrollbar height="100%">
                    <div v-if="store.explorerData.answer && store.explorerData.answer != ''" class="Xq-mt-md text-subtitle1">
                        <div Xclass="q-px-xl" v-html="compiledMarkdown(store.explorerData.answer)"></div>  
                    </div>
                </el-scrollbar>    
            </el-main>
            </el-container>
            </q-tab-panel>

            <q-tab-panel name="summary" style="height: 100%">
                <el-scrollbar height="100%">
                    <div class="q-px-xl text-subtitle1" v-html="compiledMarkdown(store.explorerData.summary)"></div>
                </el-scrollbar>
            </q-tab-panel>

            <q-tab-panel name="insights" style="height: 100%">
                <el-scrollbar height="100%">
                    <div class="prompted q-px-xl text-subtitle1" v-html="compiledMarkdown(store.explorerData.insights)"></div>
                    <!-- <q-separator spaced/> -->
                </el-scrollbar>
            </q-tab-panel>

            <q-tab-panel name="concepts" style="height: 100%">
                <el-scrollbar height="100%">
                    <div class="prompted q-px-xl text-subtitle1" v-html="compiledMarkdown(store.explorerData.concepts)"></div>
                </el-scrollbar>
            </q-tab-panel>

            <q-tab-panel name="questions" style="height: 100%">
                <el-scrollbar height="100%">
                    <div class="prompted q-px-xl text-subtitle1" v-html="compiledMarkdown(store.explorerData.questions)"></div>  
                </el-scrollbar> 
            </q-tab-panel>
        </q-tab-panels>
    </el-main>
    </el-container>

  <!-- 
    SIDE BAR
  -->
<q-drawer id="right-drawer" side="right" Xdark bordered class="q-pa-md"
      v-model="leftDrawerOpen"
      show-if-above
      :width="350"
    >
     <!-- Total tokens -->
      <!-- <total-tokens /> -->

      <!-- Include/Exclude AI Model Training Data -->
    <div Xv-if="selectedTab != 'summary'" class="p-mb-3" >
    <div class="title text-subtitle1">AI Model Training Data</div>
      <div>
        <q-btn-toggle
              v-model="store.explorerData.excludeInclude"
              @update:model-value="excludeIncludeChanged"
              Xpush
              no-caps
              Xrounded
              size="md"
              Xdense
              Xunelevated
              toggle-color="positive"
              color="grey-8"
              Xtext-color="primary"
              :options="[
                {label: 'Included', value: 'Include'},
                {label: 'Excluded', value: 'Exclude'}
              ]"
              Xstyle="padding: 5px;"
            />
            <!-- <span Xclasss="q-ml-lg" style="opacity: .7"> LLM Training Data</span> -->
            <q-btn class="q-ml-xs" icon="help_outline" flat color="info" size="sm" round>
                <q-popup-proxy Xoffset="[0, 18]">
                <div class="model-description q-pa-md">
                    <div class="text-subtitle1">Include/Exclude AI Model Training Data</div>
                    <q-separator spaced class="bg-grey-5"/>
                    <div style="max-width: 300px;">
                    <p><b>Click this toggle</b> to ask the AI Model to regenerate the explorer contents, applying the new <b>Included/Excluded</b> value.</p>
                    <p><q-icon name="info" color="positive" style="font-size: 1.3em;"/> The current setting is highligted in green.</p>
                    <p>The <b>Excluded</b> value tells the AI Model to not use its training data.</p>
                    <p>The <b>Included</b> value tells the AI Model to use its training data in addition to the provided source text.</p>
                    </div>
                </div>
                </q-popup-proxy>
            </q-btn>
        </div> 
    </div>

    <q-card id="token-usage" v-if="sessionStore.session && sessionStore.session.model" flat class="p-p-2 p-mb-2">
            <div class="subtitle text-subtitle1">AI LLM Model Used by Explorer</div>
            <div class="text-subtitle1">meta-llama/Llama-4-Scout-17B-16E-Instruct</div>
      </q-card>
      <!-- Current Exploration Source -->
      <q-card v-if="store.explorerLoading || store.explorerLoadingAsk" flat class="q-pa-sm q-mb-sm">
        <div class="subtitle Xp-mt-4">Current Exploration Source</div>
        <div class="text-subtitle1 Xtext-info">{{ explorationSource }}</div> 
      </q-card>

      <q-card v-if="!store.explorerLoading && !store.explorerLoadingAsk" flat class="q-pa-sm q-mb-sm">
        <div class="subtitle">
            <div class="title text-subtitle1">
                <span>Select Exploration Source</span>
                <q-btn class="Xq-ml-xs" icon="help_outline" flat color="info" size="sm" round>
            <q-popup-proxy Xoffset="[0, 18]">
              <div class="model-description q-pa-md">
                <div class="text-subtitle1">Exploration Source</div>
                <q-separator spaced class="bg-grey-5"/>
                <div style="max-width: 400px;">
                    <p>This setting determines the source to be used to generate the exploration results in the <b>Insights</b>, <b>Concepts</b>, and <b>Query Suggestions</b> tabs.</p>
                    <p>A source that is empty will not be selectable as the source of the exploration - it will be disabled:</p>
                    <ul>
                        <li>The <b>Context</b> option is disabled when the context is empty.</li>
                        <li>The <b>Semantic Search Results</b> option is disabled when the semantic search results are not available.</li>
                        <li>The <b>Text Search Results</b> option is disabled when the text search results are not available.</li>
                    </ul>
                    <p>One of the source options is automatically selected, based on the navigation action that brought you to this Explorer page: <br /> the <i>EXPLORER</i> tab or the <i>Explore</i> button was clicked.</p>
                </div>
              </div>
              
            </q-popup-proxy>
          </q-btn>
            </div>
        </div>
        <div class="q-mt-sm text-subtitle1">
            <q-option-group   
                :options="sourceOptions"
                type="radio"
                v-model="selectedSource"
                @update:model-value="sourceChanged"
                />
        </div>
      </q-card>
    </q-drawer>

    <!-- Report dialog-->
    <explorer-report-dlg 
      v-model="showReport" 
      :exploration-source="explorationSource" 
    />
</template>

<script setup>
    import { ref, onMounted, onBeforeMount, computed, nextTick, onUnmounted, watch } from 'vue'
    import { useRoute } from 'vue-router'
    import { useQuasar } from 'quasar'
    import { useStore } from 'src/stores/main-store';
    import { useSessionStore } from 'src/stores/session-store';
    import { useLlmStore } from 'src/stores/llm-store';
    import { useSearchStore } from 'src/stores/search-store';
    import SelectedCategories from 'src/components/SelectedCategories.vue';
    import TotalTokens from 'src/components/TotalTokens.vue'
    import { marked } from 'marked';
    import TooltipBtn from 'src/components/TooltipBtn.vue';
    import { getDocumentsText } from 'src/utils/docUtils.js';
    import ExplorerReportDlg from 'src/components/ExplorerReportDlg.vue';
    import useNotify from 'src/composables/useNotify.js';
    import { initializeTableSorting, removeEventListeners } from 'src/utils/tableSorter.js';

    const $q = useQuasar()

    const store = useStore()
    const sessionStore = useSessionStore();
    const llmStore = useLlmStore()
    const searchStore = useSearchStore()
    const { notifyProgress, notify } = useNotify()

    const route = useRoute()

    const selectedTab = ref('summary')
    const showReport = ref(false)

    const contextEmpty = computed(() => {
        return sessionStore.session && (!sessionStore.session.contextDocs || sessionStore.session.contextDocs.length == 0)
    })

    let source = route.query.source || 'context'
    if (contextEmpty.value && source == 'context') {
        if (searchStore.semanticDocs.length > 0) {
            source = 'semantic-search'
        }
        else if (searchStore.textDocs.length > 0) {
            source = 'text-search'
        }
    }
     // const selectedSource = ref([route.query.source || 'context']) // default to context
    const selectedSource = ref(source)
    const sourceOptions = computed(() => [
        // { label: 'All', value: 'all' },
        { label: 'Context', value: 'context', disable: sessionStore.session && (!sessionStore.session.contextDocs || sessionStore.session.contextDocs.length == 0) },
        { label: 'Semantic Search Results', value: 'semantic-search', disable: searchStore.semanticDocs.length == 0 },
        { label: 'Text Search Results', value: 'text-search', disable: searchStore.textDocs.length == 0 }
    ])

    async function submitUserQuery(event) {
        if (store.explorerData.query == null || store.explorerData.query == '') {
            return;
        }
        if (event) {
            if (event.shiftKey) {    
                // Allow default behavior (new line) for Shift+Enter
                return
            }
            // Prevent default behavior (new line) for Enter without Shift
            event.preventDefault()
        }

        // if (store.explorerData.query.endsWith('\n')) {
        //     store.explorerData.query = store.explorerData.query.slice(0, -1) // remove the last character (the enter key)
        // }
        store.explorerData.answer = ''; // clear the answer
        const dismiss = notifyProgress('Generating Answer ...')
        store.explorerLoadingAsk = true

        const contextText = getDocumentsText(store.explorerData.docs);
        store.explorerData.answer = await llmStore.generateAnswer(store.explorerData.query, contextText, store.explorerData.excludeInclude, null);
        dismiss()
        store.explorerLoadingAsk = false
    }

    async function excludeIncludeChanged(value, event) {
        clearExplorerData()
        await generateExplorerContents()
    }

    async function generateExplorerContents() {
        // Generated the concatenated text of all the excerpts of the documents in the current source
        const contextText = getDocumentsText(store.explorerData.docs);

        // Single progress notification for all operations
        const dismiss = notifyProgress('Generating Explorer Contents ...')
        store.explorerLoading = true
    
        const promises = []
        const dismisses = []

        // Start all promises immediately
        // Summary
        if (store.explorerData.summary == '') {
            const summaryPromise = llmStore.generateSummary(contextText).then(result => {
                // store.explorerData.summary = result
                dismisses.push(notify('Summary Ready', {timeout: 0, icon: 'check_circle'}))
                return result
            })
            promises.push(summaryPromise)
        }
        // Insights
        if (store.explorerData.insights == '') {
            const query = store.explorerData.query
            const insightsPromise = llmStore.generateAnswer(null, contextText, store.explorerData.excludeInclude, "INSIGHTS").then(result => {
                store.explorerData.insights = result
                dismisses.push(notify('Insights Ready', {timeout: 0, icon: 'check_circle'}))
                return result
            })
            promises.push(insightsPromise)
        }
        // Concepts
        if (store.explorerData.concepts == '') {
        const conceptsPromise = llmStore.generateAnswer(null, contextText, store.explorerData.excludeInclude, "CONCEPTS").then(result => {
            store.explorerData.concepts = result
                dismisses.push(notify('Concepts Ready', {timeout: 0, icon: 'check_circle'}))
                return result
            })
            promises.push(conceptsPromise)
        }
        // Query Suggestions
        if (store.explorerData.questions == '') {
            const questionsPromise = llmStore.generateAnswer(null, contextText, store.explorerData.excludeInclude, "QUESTIONS").then(result => {
                store.explorerData.questions = result
                dismisses.push(notify('Query Suggestions Ready', {timeout: 0, icon: 'check_circle'}))
                return result
            })
            promises.push(questionsPromise)
        }
        // Answer
        if (store.explorerData.answer == '' && store.explorerData.query != null && store.explorerData.query != '') {
            const answerPromise = store.explorerData.answer = await llmStore.generateAnswer(store.explorerData.query, contextText, store.explorerData.excludeInclude, null).then(result => {
                store.explorerData.answer = result
                dismisses.push(notify('Answer Ready', {timeout: 0, icon: 'check_circle'}))
                return result
            })
            promises.push(answerPromise)
        }

        // Wait for all promises to complete
        await Promise.all(promises)
        dismiss() // dismiss the progress notification
        dismisses.forEach(dismiss => dismiss()) // dismiss all notifications
        store.explorerLoading = false
    }

    function clearExplorerData() {
        store.explorerData.summary = '' // clear the summary
        store.explorerData.insights = ''; // clear the insights
        store.explorerData.concepts = ''; // clear the concepts
        store.explorerData.questions = ''; // clear the questions
        store.explorerData.answer = ''; // clear the answer
    }

    async function refresh() {
        clearExplorerData()
        await generateExplorerContents()
    }

    function compiledMarkdown(content) {
        if (content == null || content == '') {
            return ''
        }
        
        const html = marked(content);
        
        // Initialize table sorting after a short delay to ensure DOM is updated
        nextTick(() => {
            setTimeout(() => {
                removeEventListeners();
                initializeTableSorting();
            }, 100);
        });
        
        return html;
    };

    onBeforeMount(() => {
        // Don't call applyNewSource here - wait for session to be available
    })

    // Watch for session to be available before applying source
    watch(() => sessionStore.session, (newSession) => {
        if (newSession) {
            applyNewSource(selectedSource.value)
        }
    }, { immediate: true })

    // Watch for tab changes to manage copy icon listener
    watch(() => selectedTab.value, (newTab, oldTab) => {
        // Only manage listener when switching to/from questions tab
        if (newTab === 'questions' && oldTab !== 'questions') {
            // Switching TO questions tab - add listener
            document.addEventListener('click', handleCopyIconClick)
        } else if (oldTab === 'questions' && newTab !== 'questions') {
            // Switching AWAY from questions tab - remove listener
            document.removeEventListener('click', handleCopyIconClick)
        }
    })

    onMounted(async () => {
        await generateExplorerContents()
        
        // Add click event listener for copy icons only if starting on questions tab
        if (selectedTab.value === 'questions') {
            document.addEventListener('click', handleCopyIconClick)
        }
    })

    onUnmounted(() => {
        removeEventListeners();
        document.removeEventListener('click', handleCopyIconClick);
    })

    async function sourceChanged(value) {
        applyNewSource(value)
        await generateExplorerContents()
        
        // If currently on questions tab, remove and re-add listener after source change
        if (selectedTab.value === 'questions') {
            document.removeEventListener('click', handleCopyIconClick)
            document.addEventListener('click', handleCopyIconClick)
        }
    }

    function applyNewSource(source) {
        store.currentExplorerSource = source
        if (source == 'context' && sessionStore.session) {
            store.explorerData = sessionStore.session.explorer
            store.explorerData.docs = sessionStore.session.contextDocs
        }
        else if (source == 'semantic-search') {
            store.explorerData = store.explorerSemanticSearchData
            store.explorerData.docs = searchStore.semanticDocs
        }
        else if (source == 'text-search') {
            store.explorerData = store.explorerTextSearchData
            store.explorerData.docs = searchStore.textDocs
        }
    }


    const explorationSource = computed(() => {
        if (store.currentExplorerSource == 'context') {
            return 'Context'
        }
        else if (store.currentExplorerSource == 'semantic-search') {
            return 'Semantic Search Results'
        }
        else if (store.currentExplorerSource == 'text-search') {
            return 'Text Search Results'
        }
    })

    async function copyToClipboard() {
        let text = ''
        let type = ''
        if (selectedTab.value == 'summary') {
            type = 'Summary'
            text = store.explorerData.summary
        }
        else if (selectedTab.value == 'insights') {
            type = 'Insights'
            text = store.explorerData.insights
        }
        else if (selectedTab.value == 'concepts') {
            type = 'Concepts'
            text = store.explorerData.concepts
        }
        else if (selectedTab.value == 'questions') {
            type = 'Query Suggestions'
            text = store.explorerData.questions
        }
        else if (selectedTab.value == 'ask') {
            type = 'Answer'
            text = store.explorerData.answer
        }

        await navigator.clipboard.writeText(text)
        notify(type + ' copied to clipboard.')
    }

    async function handleCopyIconClick(e) {
        if (e.target.classList.contains('copy-icon')) {
            const li = e.target.closest('li');
            if (li) {
                // Extract text content from the li element, excluding the icon
                const textToCopy = li.textContent.replace('assignment', '').replace('check', '').trim();
                if (textToCopy) {
                    await navigator.clipboard.writeText(textToCopy)
                    notify('Copied query suggestion to clipboard.')
                }
            }
        }
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

:deep() .prompted h6 {
    margin-top: 10px !important;
    margin-bottom: 10px !important;
    font-size: 1.2rem !important;
    font-weight: 400 !important;
}

</style>