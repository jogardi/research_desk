<template>
    <div v-if="sessionStore.session.categories.length > 0" class="p-d-flex p-justify-content-between p-align-items-center">
      <q-input class="col col-grow p-pb-0"
        v-model="searchStore.textSearchQuery"
        @keydown.enter.stop="submitUserQuery"
        color="primary"
        outlined
        rounded
        dense
        clearable
        autogrow
        type="textarea"
        label="Enter your search terms (Google-like) to search the knowledgebase"
        Xhint="* Set query parameters in the Context Builder Setup sidebar --->"
        :disable="store.textSearchLoading"
        :loading="store.textSearchLoading"
      >
        <template v-slot:append>
          <!-- <div class="p-d-flex p-justify-content-between p-align-items-center"> -->
            <q-btn
              @click="submitUserQuery"
              class="p-ml-1"
              :disabled="searchStore.textSearchQuery == null || searchStore.textSearchQuery == '' || store.textSearchLoading"
              Xsize="sm"
              dense
              rounded
              flat
              color="primary"
              icon="search"
            />

            <q-btn
              @click="showTextSearchHelp = true"
              class="p-ml-1"
              size="sm"
              dense
              rounded
              flat
              color="info"
              icon="help"
            />
          <!-- </div> -->
        </template>
      </q-input>
      <div class="p-ml-2">
        <q-option-group
            v-model="tablesImages"
            @update:model-value="updateTablesImages"
          :options="[
            { label: 'Tables', value: 'table' },
            { label: 'Images', value: 'image' },
          ]"
          color="primary"
          type="checkbox"
          inline
          dense
          size="sm"
        />
      </div>

      <!-- <q-btn v-if="store.textSearchLoading" @click="abort()" icon="stop" 
        Xstyle="font-size: 1rem" class="p-ml-2" color="negative" size="sm" round Xdense Xflat Xoutline>
      </q-btn> -->

      <!-- Text Search Help Dialog -->
    <text-search-help-dlg v-model="showTextSearchHelp" />
    </div>
  </template>
  
  <script setup>
    import { ref } from 'vue'
    import { useSessionStore } from 'src/stores/session-store';
    import { useStore } from 'src/stores/main-store';
    import { useCategoryStore } from 'src/stores/category-store';
    import { useSearchStore } from 'src/stores/search-store';
    import TextSearchHelpDlg from 'src/components/context-builder/TextSearchHelpDlg.vue';

    const searchStore = useSearchStore()
    const store = useStore()
    
    const props = defineProps({
      
    })
    
    const sessionStore = useSessionStore()
    
    const emit = defineEmits(['submit'])
    
    const tablesImages = ref([])

    const showTextSearchHelp = ref(false)
    
    async function submitUserQuery (event) {
      tablesImages.value = []

        if (searchStore.textSearchQuery == null || searchStore.textSearchQuery == '') {
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

    function updateTablesImages(value) {
      // join value array elements with " or " as a separator:
      let query = value.join(' OR ')
      searchStore.textSearchQuery = query
    }

    async function abort() {
        store.textSearchLoading = false
    }
  </script>


    