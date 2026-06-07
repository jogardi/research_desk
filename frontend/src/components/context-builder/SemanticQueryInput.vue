<template>
    <div v-if="sessionStore.session.categories.length > 0" class="p-d-flex p-justify-content-between p-align-items-center">
      <q-input class="col col-grow p-pb-0"
        v-model="searchStore.semanticSearchQuery"
        @keydown.enter.stop="submitUserQuery"
        color="primary"
        outlined
        rounded
        dense
        clearable
        autogrow
        type="textarea"
        label="Enter your query to search the knowledgebase"
        Xhint="* Set query parameters in the Context Builder Setup sidebar --->"
        :disable="store.semanticSearchLoading"
        :loading="store.semanticSearchLoading"
      >
        <template v-slot:append>
          <div class="p-d-flex p-justify-content-between p-align-items-center">
            <q-btn
              @click="submitUserQuery"
              class="p-ml-1"
              :disabled="searchStore.semanticSearchQuery == null || searchStore.semanticSearchQuery == '' || store.semanticSearchLoading"
              Xsize="sm"
              dense
              rounded
              flat
              color="primary"
              icon="search"
            />
            <q-btn @click="getSuggestedCategories()" v-if="searchStore.semanticSearchQuery" Xlabel="Suggest Categories" flat Xoutline 
              color="primary" size="sm" dense class="p-ml-1" no-caps icon="category" style="font-size: .8rem">
              <q-menu anchor="bottom right" self="top right" class="p-p-2">
                <div v-if="suggestedCategories.length > 0" class="p-p-1">
                  <div class="text-subtitle2 subtitle p-pb-2" Xstyle="text-align: center;">Suggested Categories:</div>
                  <div class="p-d-flex p-flex-column" style="max-height: 200px; overflow-y: auto;">
                    <div v-for="category in suggestedCategories" :key="category.value" style="opacity: .9">
                      <q-checkbox v-model="selectedSuggestedCategories" :label="category" :val="category" dense size="xs" />
                      <q-btn @click="getCategoryDescription(category)" icon="visibility" color="grey-6" size="xs" flat>
                        <q-popup-proxy anchor="bottom middle" self="top right" style="width: 400px;" Xclass="p-p-3">
                          <div class="p-pl-2 p-pt-2">Category Description</div>
                          <el-scrollbar height="300px" class="p-p-3">
                            <div v-html="marked(catDescription)"></div>
                          </el-scrollbar>
                        </q-popup-proxy>
                      </q-btn>
                    </div>
                    <div class="p-d-flex p-justify-content-end">
                      <q-btn @click="addSuggestedCategories()" label="Add Selected Categories" v-close-popup
                        :disabled="selectedSuggestedCategories.length == 0"
                        no-caps flat color="positive" Xsize="sm" class="q-mt-md" />
                    </div>
                  </div>
                </div>
                <div v-if="gettingSuggestedCategories"class="text-subtitle1 text-info p-p-0" style="text-align: center;">
                  Processing ....
                </div>
                <div v-if="suggestedCategories.length == 0 && !gettingSuggestedCategories">
                  <div class="text-subtitle1 text-info p-p-0" style="text-align: center;">
                    No new suggested categories related to the current query.
                  </div>
                </div>
              </q-menu>
            </q-btn>
            <q-btn v-if="store.suggestedQueries.length > 0" flat Xoutline 
              color="primary" size="sm" dense class="p-ml-1" no-caps icon="keyboard_arrow_down" style="font-size: .8rem">
              <q-menu anchor="bottom right" self="top right" :offset="[0, 15]" class="p-p-2">
                <q-list dense>
                  <q-item v-for="suggestedQuery in store.suggestedQueries" :key="suggestedQuery" 
                    @click="searchStore.semanticSearchQuery = suggestedQuery" clickable  v-close-popup>
                    <q-item-section>
                      <q-item-label>{{ suggestedQuery }}</q-item-label>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-menu>
            </q-btn>
          </div>
        </template>
      </q-input>

      <!-- <q-btn v-if="store.semanticSearchLoading" @click="abort()" icon="stop" 
        Xstyle="font-size: 1rem" class="p-ml-2" color="negative" size="sm" round Xdense Xflat Xoutline>
      </q-btn> -->
    </div>
  </template>
  
  <script setup>
    import { ref, onMounted } from 'vue'
    import { useStore } from 'src/stores/main-store';
    import { useSessionStore } from 'src/stores/session-store';
    import { useCategoryStore } from 'src/stores/category-store';
    import { useSearchStore } from 'src/stores/search-store';
    import { useLlmStore } from 'src/stores/llm-store';
    import { getDocumentsText } from 'src/utils/docUtils.js';
    import { marked } from 'marked';


    const searchStore = useSearchStore()
    const llmStore = useLlmStore()
    
    const props = defineProps({
    
    })

    const suggestedCategories = ref([])

    const selectedSuggestedCategories = ref([])

    const catDescription = ref('')
    const gettingSuggestedCategories = ref(false)
    
    const store = useStore()
    const sessionStore = useSessionStore()
    const categoryStore = useCategoryStore()
    
    const emit = defineEmits(['submit'])

    onMounted(async() => {
      if (store.suggestedQueries.length == 0) {
        const contextText = getDocumentsText(sessionStore.session.contextDocs);
        if (contextText.length > 0) {
          await llmStore.generateSuggestedQueries(contextText)
        }
      }
    })
    
    async function submitUserQuery (event) {
        if (searchStore.semanticSearchQuery == null || searchStore.semanticSearchQuery == '') {
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
        
        // send the query to the parent component:
        emit('submit')
    }

    function addSuggestedCategories() {
      selectedSuggestedCategories.value.forEach(categoryPath => {
        const categoryId = _findCategoryIdByPath(categoryPath)
        if (categoryId) {
          sessionStore.session.categories.push(categoryId)
          categoryStore.selectedCategories.push({ id: categoryId, label: categoryPath })
        }
      })
    }

    function _findCategoryIdByPath(path) {
      // Split the path string into parts
      const parts = path.split('/');

      // Start at the root level of the categories
      let nodes = categoryStore.categoryTreeData;
      let resultId = null;
 
      // Traverse the tree by matching each part to the label in the current list of nodes
      for (const part of parts) {
        // Find the node with a label that matches the current part
        const node = nodes.find(item => item.label === part);
        if (!node) {
          // If not found, return null (or you could throw an error)
          return null;
        }
        // Save the id from the matched node
        resultId = node.id;
        // Descend into the children if available, otherwise use an empty array
        nodes = node.children || [];
      }

      return resultId;
  }

    async function getCategoryDescription(category) {
        catDescription.value = await store.getCategoryDescription(category)
    }

    async function getSuggestedCategories() {
      gettingSuggestedCategories.value = true
      suggestedCategories.value = await searchStore.getSuggestedCategories(searchStore.semanticSearchQuery)
      gettingSuggestedCategories.value = false
      
        if (suggestedCategories.value.length == 0) {
            return;
        }

        // Remove the categories that are already selected
        categoryStore.selectedCategories.forEach(category => {
          suggestedCategories.value = suggestedCategories.value.filter(c => c != category.label)
        })

        selectedSuggestedCategories.value = []
    }

    async function abort() {
        store.semanticSearchLoading = false
    } 
  </script>


    
