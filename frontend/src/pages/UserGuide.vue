<template>
    <el-container style="height: 100vh" id="user-guide" class="p-pt-0">
        <el-header height="auto" class="fixed-header p-py-1">
            <!-- Tabs -->
            <q-toolbar id="text-h6" class="p-pa-0 p-mt-0">
                <q-toolbar-title style="font-size: 1.5rem; text-align: left;">User Guide</q-toolbar-title>
            </q-toolbar>
        </el-header>
        <el-main class="bg-content-area p-p-0">
            <!-- Sections -->
            <div ref="scrollbarRef" class="scrollable-content p-px-6 p-pt-0" style="height: 100%; padding-bottom: 100px;">
                <div id="workflow" class="p-mt-5">
                    <h1>Introduction: Iterative Workflow</h1>
                    <ol>
                        <li><strong>Organize</strong>: Use thought flows to manage multiple research trains of thought.</li>
                        <li><strong>Define Scope</strong>: Choose categories.</li>
                        <li><strong>Search</strong>: Search for meaningful information.</li>
                        <li><strong>Build</strong>: Curate context using the Context Builder.</li>
                        <li><strong>Explore</strong>: Quick view for key Insights.</li>
                        <li><strong>Engage</strong>: Query AI-LLMs via Chat.</li>
                        <li><strong>Iterate</strong>: Continue to refine and explore further.</li>
                    </ol>
                </div>
                <div id="organize" class="p-mt-5">
                    <h1>Organize</h1>
                    <ul>
                        <li>A thought flow is a collection of related thoughts. It provides a focused way to organize your research.</li>
                        <li>When you discover a new train of thought, fork the existing thought flow to explore multiple paths in parallel.</li>
                    </ul>
                </div>
                <div id="scope" class="p-mt-5">
                    <h1>Define Scope</h1> 
                    <ul>
                        <li>The Category Selector allows researchers to define the scope of their search by selecting specific categories from the knowledge base.</li>
                        <li>This ensures that searches are focused and relevant to the research objectives.</li>
                        <li>Categories can be added or removed anytime during the research process.</li>
                    </ul>
                </div>
                <div id="search" class="p-mt-5">
                    <h1>Search</h1> 
                    <p>The search feature allows you to explore the knowledge base by searching for relevant information. Multiple searches can be performed and search results can be curated into the context tab.</p>
                        <h2 id="ss">Semantic Search</h2>
                            <ul>
                                <li>Semantic search can significantly enhance the discovery process by understanding the intent behind queries, identifying related concepts, and providing comprehensive results that are contextually relevant.</li>
                                <li>This makes it a powerful tool for uncovering deeper insights and connections within large datasets.</li>
                                <li>An example of a semantic search query is "What is the relationship between the use of AI in healthcare and the cost of healthcare?" This would return results that are relevant to the query, such as "AI can help reduce the cost of healthcare by improving efficiency and reducing errors."</li>
                
                            </ul>
                            <h3 id="ss-config">Configuration</h3>
                            <ul>
                                <li>Top-K: The maximum number of results per category.</li>
                                <li>Minimum Similarity Score: The minimum similarity score for a result to be considered relevant.</li>
                            </ul>
                            <h3 id="ss-suggestions">Search Suggestions</h3>
                            <p>AI generated suggestions.</p>
                            <ul>
                                <li><q-icon name="keyboard_arrow_down" color="primary" />Recommend queries based on the current context.</li>
                                <li><q-icon name="category" color="primary"/>Recommend categories based on the search query.</li>
                            </ul>
                        <h2 id="fts">Text Search</h2>
                            <ul>
                                <li>Text search is a powerful tool for finding specific information within a large dataset.</li>
                                <li>Use text search when searching for named entities ('John', 'Jane', 'etc.') and rare terms ('Bioinformatics')</li>
                                <li>Boolean (AND/OR/NOT) and Near (search term distance) operators are supported.</li>
                                <li>
                                    <div class="q-option-group q-gutter-x-sm q-option-group--inline" role="group">
                                        <div>
                                            <div class="q-checkbox cursor-pointer no-outline row inline no-wrap items-center q-checkbox--dark q-checkbox--dense" tabindex="0" role="checkbox" aria-label="Tables" aria-checked="false">
                                                <div class="q-checkbox__inner relative-position non-selectable q-checkbox__inner--falsy" aria-hidden="true" style="font-size: 35px;">
                                                    <input class="hidden q-checkbox__native absolute q-ma-none q-pa-none" type="checkbox">
                                                    <div class="q-checkbox__bg absolute">
                                                        <svg class="q-checkbox__svg fit absolute-full" viewBox="0 0 24 24">
                                                            <path class="q-checkbox__truthy" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59"></path>
                                                            <path class="q-checkbox__indet" d="M4,14H20V10H4"></path>
                                                        </svg>
                                                    </div>
                                                </div>
                                                <span class="no-outline" tabindex="-1"></span>
                                                <div class="q-checkbox__label q-anchor--skip">Tables</div>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="q-checkbox cursor-pointer no-outline row inline no-wrap items-center q-checkbox--dark q-checkbox--dense" tabindex="0" role="checkbox" aria-label="Images" aria-checked="false">
                                                <div class="q-checkbox__inner relative-position non-selectable q-checkbox__inner--falsy" aria-hidden="true" style="font-size: 35px;">
                                                    <input class="hidden q-checkbox__native absolute q-ma-none q-pa-none" type="checkbox">
                                                    <div class="q-checkbox__bg absolute">
                                                        <svg class="q-checkbox__svg fit absolute-full" viewBox="0 0 24 24">
                                                            <path class="q-checkbox__truthy" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59"></path>
                                                            <path class="q-checkbox__indet" d="M4,14H20V10H4"></path>
                                                        </svg>
                                                    </div>
                                                </div>
                                                <span class="no-outline" tabindex="-1"></span>
                                                <div class="q-checkbox__label q-anchor--skip">Images</div>
                                            </div>
                                        </div>
                                    </div>
                                    Check tables and/or images to return all of the tables and/or images.
                                </li>
                                
                            </ul>
                        <h2 id="search-results">Search Results</h2>
                        
                            <ul>
                                <li>These are the excerpts, grouped by category/artifact, that match the search query.</li>
                                <li>The title is dynamically AI generated based on the excerpts within the artifact.</li>
                                <li>Color Coding</li>
                                    <ul>
                                        <li><span class="chunk-text"><b>Semantic match on the nouns in the search query</b></span></li>
                                    </ul>
                                    <ul>
                                        <li><span class="hilite-sentence">Text matching on the query (hit)</span></li>
                                    </ul>
                                    <ul>
                                        <li><span class="chunk-text">Surrounding contextual text adjacent to the hit</span></li>
                                    </ul>
                                <li><q-icon name="description" color="info" /> Open the source artifact in a new tab.</li>
                                <li><button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-positive text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">explore</i><span class="block">Explore</span><!----></span></button>
                                    Explore the search results in the <a href="#explorer">Explorer tab</a>.</li>
                                    
                                
                            </ul>
                            <h3 id="ss-excerpt-actions">Excerpt Actions</h3>
                            <ul>
                                <li>Move excerpt to the Context</li>
                                <li>Stash excerpt for later reference (not included in the context)</li>
                                <li>Remove excerpt from the search results</li>
                                <li>View the excerpt in the source document</li>
                                <li>Search for similar content as the excerpt</li>
                            </ul>

                            <p>
                                <!-- <q-icon name="info" color="info" />  -->
                                The <button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">playlist_add</i><!----></span></button> Move , 
                                <button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">quiz</i><!----></span></button> Stash
                                and <button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-negative text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">delete</i><!----></span></button> Remove 
                                actions can be performed on multiple excerpts at once by <button data-v-5afb4d97="" class="q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense text-subtitle2 p-mr-2 q-btn--active" tabindex="0" type="button" xsize="sm"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon on-left notranslate material-icons" aria-hidden="true" role="img">check</i><span class="block">Check All</span></span></button>
                                checking the desired excerpts and then clicking the cooresponding button in the toolbar.
                            </p>
                            
                            
                </div>
                <div id="stash" class="p-mt-5">
                    <h1>Stash</h1>
                    <ul>
                        <li>Stash excerpts for later reference.</li>
                        <li>They are not included in the context.</li>
                    </ul>
                </div>
                <div id="context" class="p-mt-5">
                    <h1>Context</h1> 
                    <ul>
                        <li>These are the excerpts, grouped by category/artifact, that were moved from the search results.</li>
                        <li>The context tab is where you can curate the most relevant search results into a focused context for further exploration.</li>
                        <li>The context is presented to the AI models while exploring or chatting to provide a more focused and relevant response.</li>
                      
                        
                                <li>The title is dynamically AI generated based on the excerpts within the artifact.</li>
                                <li>Color Coding</li>
                                    <ul>
                                        <li><span class="chunk-text"><b>Semantic match on the nouns in the search query</b></span></li>
                                    </ul>
                                    <ul>
                                        <li><span class="hilite-sentence">Text matching on the query (hit)</span></li>
                                    </ul>
                                    <ul>
                                        <li><span class="chunk-text">Surrounding contextual text adjacent to the hit</span></li>
                                    </ul>
                                <li><q-icon name="description" color="info" /> Open the source artifact in a new tab.</li>
                                <li><button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-positive text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">explore</i><span class="block">Explore</span><!----></span></button>
                                    Explore the context in the <a href="#explorer">Explorer tab</a>.</li>
                    </ul>
                    <h2 id="ctx-excerpt-actions">Excerpt Actions</h2>
                    <ul>
                        <li>Make excerpt more concise (does not affect the original excerpt, only the context)</li>
                        <li>Edit the excerpt (does not affect the original excerpt, only the context)</li>
                        <li>Restore the original excerpt (if edited or concise)</li>
                        <li>Stash excerpt for later reference (not included in the context)</li>
                        <li>Remove excerpt from the context</li>
                        <li>View the excerpt in the source document</li>
                        <li><i data-v-5afb4d97="" class="q-icon text-info notranslate material-icons" aria-hidden="true" role="presentation" style="font-size: 24px; cursor: pointer;">playlist_add_check</i> Mark as reviewed</li>
                        <li><span class="q-btn__content text-center col -anchor--skip"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">sticky_note_2</i></span> Add sticky note</li>
                    </ul>
                        
                           
                    <p>
                        <!-- <q-icon name="info" color="info" />  -->
                        The <button data-v-5afb4d97="" class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">short_text</i><!----></span></button> Concise , 
                        <button data-v-5afb4d97="" class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">subject</i><!----></span></button> Restore Original Text , 
                        <button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">quiz</i><!----></span></button> Stash
                        and <button class="q-btn q-btn-item non-selectable no-outline q-btn--standard q-btn--rectangle bg-negative text-white q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense" tabindex="0" type="button" disabled="" style="font-size: 10px;"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon notranslate material-icons" aria-hidden="true" role="img">delete</i><!----></span></button> Remove 
                        actions can be performed on multiple excerpts at once by <button data-v-5afb4d97="" class="q-btn q-btn-item non-selectable no-outline q-btn--flat q-btn--rectangle text-primary q-btn--actionable q-focusable q-hoverable q-btn--no-uppercase q-btn--dense text-subtitle2 p-mr-2 q-btn--active" tabindex="0" type="button" xsize="sm"><span class="q-focus-helper"></span><span class="q-btn__content text-center col items-center q-anchor--skip justify-center row"><i class="q-icon on-left notranslate material-icons" aria-hidden="true" role="img">check</i><span class="block">Check All</span></span></button>
                        checking the desired excerpts and then clicking the cooresponding button in the toolbar.
                    </p>   
                            
                </div>
                <div id="explorer" class="p-mt-5">
                    <h1>Explorer</h1>
                    <ul>
                        <li>The explorer provides a high level overview of the context. </li>
                        <li>Use this to quickly get a sense of the context and then use the context builder to further refine the context.</li>
                        <li>Include/Exclude AI-LLM training data. Exclude the AI-LLM training data helps the model to focus on your provided context.</li>
                        <li>Explor semantic search results, full text search results or your context.</li>
                        <li>The explorer is a tool to help you get a sense of the context and then use the context builder to further refine the context.</li>
                    </ul>
                     <h2 id="explorer-actions">Explorer Actions</h2>
                     <ul>
                        <li><strong>Summary</strong>: Summarize the context.</li>
                        <li><strong>Insights</strong>: Provide key insights.</li>
                        <li><strong>Query Suggestions</strong>: Suggest queries for the AI-LLM.</li>
                        <li><strong>Ask</strong>: This allows you to ask the AI-LLM a single question (not chat) about the context. Again, this is helpfult when evaluating your context.</li>                       
                    </ul>
                </div>
                <div id="chat" class="p-mt-5">
                    <h1>Chat</h1>
                    <ul>
                        <li>Chat with multiple AI-LLMMs with the context you created.</li>
                    </ul>
                    <h2 id="chat-config">Chat Configuration</h2>
                    <ul>
                        <li><strong>Include/Exclude AI-LLM training data</strong>. Exclude the AI-LLM training data helps the model to focus on your provided context.</li>
                        <li><strong>Model Token Usage</strong> helps you to track if you are withing the model's token limit.</li>
                        <li><strong>Role for the AI Model</strong> provides a role helps guide the behavior, tone, and knowledge boundaries of an AI model during a conversation or task. It sets the persona the model should adopt, which can significantly affect its responses</li>
                        <li><strong>Temperature</strong> helps you to control the creativity of the AI-LLM. Lower temperature makes the model more focused and deterministic, while higher temperature makes the model more creative and random.</li>   
                        
                        
                    </ul>
                </div>
                <div id="chat-tools" class="p-mt-5">
                    <h1>Chat Tools</h1>
                    <ul>
                        <li>Search knowledgebase for relevant information.</li>
                        <li>Load entire page. This allows the AI to see an entire page of it's choosing with it's vision capability. Meaning it can see figures and all text on the page.</li>
                        <li>Import pdf from hyperlink. You can provide a link to a public pdf to the AI or the AI could access a link to a pdf that it sees in the knowledgebase.</li>
                    </ul>

                </div>
            </div>
        </el-main>
    </el-container>

    <q-drawer id="left-drawer" dark bordered class="q-pa-md"
      v-model="leftDrawerOpen"
      show-if-above
      :width="350">
      <el-anchor id="user-guide-anchor" class="p-mr-3"
                :container="scrollbarRef"
                direction="vertical"
                type="default"
                :offset="20"
                :bounds="0"
                @click.prevent
                :marker="false"
                :select-scroll-top="true">
            <el-anchor-link href="#workflow" title="Introduction: Iterative Workflow" @click.prevent="scrollToSection('workflow')" />
            <el-anchor-link href="#organize" title="Organize" @click.prevent="scrollToSection('organize')" />
            <el-anchor-link href="#scope" title="Define Scope" @click.prevent="scrollToSection('scope')" />
            <!-- <el-anchor-link href="#context" title="Context" @click.prevent="scrollToSection('context')">
                <template #sub-link>    
                    <el-anchor-link href="#ctx-excerpt-actions" title="Excerpt Actions" @click.prevent="scrollToSection('ctx-excerpt-actions')" />
                </template>
            </el-anchor-link> -->
            <el-anchor-link href="#search" title="Search" @click.prevent="scrollToSection('search')">
                <template #sub-link>
                    <el-anchor-link href="#ss" title="Semantic Search" @click.prevent="scrollToSection('ss')">
                        <template #sub-link>    
                            <el-anchor-link href="#ss-config" title="Configuration" @click.prevent="scrollToSection('ss-config')" />
                            <el-anchor-link href="#ss-suggestions" title="Search Suggestions" @click.prevent="scrollToSection('ss-suggestions')" />
                        </template>
                    </el-anchor-link>
                    <el-anchor-link href="#fts" title="Text Search" @click.prevent="scrollToSection('fts')" />
                    <el-anchor-link href="#search-results" title="Search Results" @click.prevent="scrollToSection('search-results')">
                        <template #sub-link>    
                            <el-anchor-link href="#ss-excerpt-actions" title="Excerpt Actions" @click.prevent="scrollToSection('ss-excerpt-actions')" />
                        </template>
                    </el-anchor-link>
                </template>
                </el-anchor-link>
                <el-anchor-link href="#stash" title="Stash" @click.prevent="scrollToSection('stash')" />
                <el-anchor-link href="#context" title="Context" @click.prevent="scrollToSection('context')">
                    <template #sub-link>
                        <el-anchor-link href="#ctx-excerpt-actions" title="Excerpt Actions" @click.prevent="scrollToSection('ctx-excerpt-actions')" />
                    </template>
                </el-anchor-link>
                <el-anchor-link href="#explorer" title="Explorer" @click.prevent="scrollToSection('explorer')" >
                <template #sub-link>
                        <el-anchor-link href="#explorer-actions" title="Explorer Actions" @click.prevent="scrollToSection('explorer-actions')" />
                    </template>
                </el-anchor-link>
                <el-anchor-link href="#chat" title="Chat" @click.prevent="scrollToSection('chat')" >
                    <template #sub-link>
                        <el-anchor-link href="#chat-config" title="Chat Configuration" @click.prevent="scrollToSection('chat-config')" />
                    </template>
                </el-anchor-link>
                <el-anchor-link href="#chat-tools" title="Chat Tools" @click.prevent="scrollToSection('chat-tools')" />
        </el-anchor>
    </q-drawer>
</template>

<script setup>
import { ref, onMounted } from 'vue';
// import { useStore } from 'src/stores/main-store';

// const store = useStore()

const leftDrawerOpen = ref(true)
const scrollbarRef = ref(null)

onMounted(() => {
  setTimeout(() => {
    const scrollbar = scrollbarRef.value
    if (scrollbar) {
        // calc the offset of the intro section relative to the scrollable container
        const introSection = document.getElementById('intro')
        const containerRect = scrollbar.getBoundingClientRect()
        const elementRect = introSection.getBoundingClientRect()
        const offset = elementRect.top - containerRect.top + scrollbar.scrollTop
        console.log("offset: " + offset)
        scrollbar.scrollTop = offset - 25
    }
  }, 100)
})

const scrollToSection = (targetElementId) => {
  const scrollbar = scrollbarRef.value
  const targetElement = document.getElementById(targetElementId)
  
  if (scrollbar && targetElement) {
    // Calculate position relative to the scrollable container
    const containerRect = scrollbar.getBoundingClientRect()
    const elementRect = targetElement.getBoundingClientRect()
    const offsetTop = elementRect.top - containerRect.top + scrollbar.scrollTop
    scrollbar.scrollTop = offsetTop
  }
}
</script>

<style scoped>
.fixed-header {
    position: sticky;
    top: 50px;
    z-index: 1000;
    /* background-color: #556677; */
    /* border-bottom: 1px solid #e0e0e0; */
    /* padding-bottom: 10px; */
}

.scrollable-content {
    height: 100%; /*calc(100vh - 100px);*/
    overflow-y: auto;
    padding-top: 20px;
    padding-bottom: 20px;
}

:deep() #user-guide-anchor .el-anchor__link {
    font-size: 1.1rem !important;
    font-weight: 400 !important;
}

.scrollable-content h1 {
    font-size: 1.5rem !important;
    font-weight: 400;
    color: var(--q-info) !important;
    opacity: 0.8;
    /* padding-bottom: 0px !important;
    padding-top: 0px !important;*/
    margin-bottom: 0px !important;
    margin-top: 0px !important; 
    line-height: 1.6;
}
.scrollable-content h2 {
    font-size: 1.2rem !important;
    font-weight: 425;
    color: var(--q-info) !important;
    opacity: 0.8;
}
.scrollable-content h3 {
    font-size: 1.1rem !important;
    font-weight: 400;
    color: var(--q-info) !important;
    opacity: 0.8;
}

.scrollable-content p, li, ol{
    font-size: 1.1rem !important;
    font-weight: 400;
    opacity: 0.9;
    line-height: 1.3;
    margin-bottom: 5px !important;
}

.q-icon {
    font-size: 1.1rem !important;
}

</style>