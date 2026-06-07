<template>
  <el-dialog v-model="dialogVisible" :width="1000" :show-close="false" :top="dialogTop + 'px'" class="dialog-body notes-report">
    <!-- dialog header -->
    <template #header="{ close, titleId, titleClass }">
      <q-toolbar>
        <q-toolbar-title style="font-size: 1rem;"><q-icon name="description" class="p-ml-2 p-mr-2"></q-icon>
          Report - {{ explorationSource }}
      </q-toolbar-title>
          <q-space />
          <!-- <tooltip-btn tooltip="Download as PDF" flat dense color="positive" icon="picture_as_pdf" size="md" /> -->
          <!-- <tooltip-btn tooltip="Share" icon="share" flat size="sm" color="positive" class="p-mr-1" Xstyle="font-size: .8rem;"></tooltip-btn> -->
          <q-separator vertical inset class="p-ml-3 p-mr-1" />
          <q-btn flat round dense color="primary" icon="close" @click="close" />
      </q-toolbar>
    </template>

    <!-- dialog body -->
    <div class="p-d-flex p-justify-center"  :style="{ height: dialogHeight + 'px' }">
      <el-scrollbar height="100%" class="p-pt-2 p-pb-4 p-px-4" style="width: 90% !important;">
        <!-- Summary -->
        <div id="summary" v-if="!isSummaryEmpty" class="p-mx-auto">
            <div class="subtitle text-h5">Summary</div>
            <hr />
            <div v-html="marked(store.explorerData.summary)" style="font-size: 1rem;"></div>
        </div>
        <!-- Key Insights -->
        <div id="insights" v-if="store.explorerData.insights != ''" class="p-mx-auto p-mt-4">
            <div class="subtitle text-h5">Insights</div>
            <hr />
            <div v-html="marked(store.explorerData.insights)" style="font-size: 1rem;"></div>
        </div>
        <!-- Main Concepts -->
        <div id="concepts" v-if="store.explorerData.concepts != ''" class="p-mx-auto p-mt-4">
            <div class="subtitle text-h5">Concepts</div>
            <hr />
            <div v-html="marked(store.explorerData.concepts)" style="font-size: 1rem;"></div>
        </div>
      </el-scrollbar>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, defineAsyncComponent, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useStore } from 'src/stores/main-store';
import { marked } from 'marked';
import TooltipBtn from 'src/components/TooltipBtn.vue'

const $q = useQuasar() 
const store = useStore()

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  explorationSource: {
    type: String,
    default: ''
  }
})

const dialogTop = ref(0)
const dialogHeight = ref(0)

onMounted(() => {
  // Simple dialog positioning - calculated once
  const explorerTabs = document.getElementById('explorer-tabs')
  if (explorerTabs) {
    dialogTop.value = explorerTabs.offsetTop + explorerTabs.offsetHeight + 10
    dialogHeight.value = (window.innerHeight - dialogTop.value) * .75
  }
})

const isSummaryEmpty = computed(() => {
    const noSummary = "There is no context text provided to summarize. Please provide the necessary text, and I'll be happy to assist you with a summary."
    return store.explorerData.summary == '' || store.explorerData.summary == noSummary
})

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
// Emits
const emit = defineEmits(['update:modelValue'])

// Computed property to handle v-model
const dialogVisible = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
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
  height: calc(100% - 20px); /* Adjust based on toolbar height */
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