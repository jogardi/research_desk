<template>
    <q-card class="notes-report p-p-0" style="height: 100%; width: 100%;">
        <el-container style="height: 100%;">
            <el-header style="height: auto; padding: 0;">
                <q-toolbar class="fixed-toolbar">
                    <q-toolbar-title style="font-size: 1rem;"><q-icon name="account_tree" class="p-ml-2 p-mr-2"></q-icon>Knowledgebase Tree</q-toolbar-title>
                    <q-space />
                    <div v-if="kbBuilderStatus == 'Processing'" class="flex items-center p-mr-3">
                      <tooltip-btn tooltip="Refresh injestion status" @click="showKBBuilderStatus()" icon="refresh" color="positive"  flat no-caps size="sm"  dense class="q-mr-sm" />
                      <span class="text-info">{{ kbBuilderStatus }} ...</span>
                    </div>
                    <tooltip-btn v-else tooltip="Run Knowledgebase Builder" @click="runKBBuilder()" label="Refresh Knowledgebase" icon="refresh" color="primary"  Xoutline no-caps size="md"  dense class="q-mr-sm" />
                    <q-btn Xflat @click="collapseExpandAll()" :label="treeExpanded? 'Collapse' : 'Expand'" color="primary" flat Xoutline no-caps size="md"  dense class="q-mr-sm" :icon="treeExpanded? 'expand_less' : 'expand_more'" />
                    <q-separator vertical inset class="p-ml-3 p-mr-1" />
                    <q-btn flat round dense color="primary" icon="close" v-close-popup />
                </q-toolbar>
            </el-header>
            
            <el-main class="bg-content-area" style="height: 100%;">
                <el-scrollbar always height="100%" style="padding-left: 20px;" v-if="store.docTreeData && store.docTreeData.length > 0">
                    <el-tree 
                    ref="treeRef"
                    class="bg-content-area"
                    :data="store.docTreeData"
                    node-key="id"
                    default-expand-all
                    :indent="0"
                    :expand-on-click-node="false"
                    :props="defaultProps"
                    >
                    <template #default="{ node, data }">
                        <span :class="!node.isLeaf ? 'category-color' : ''" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 90%; display: inline-block;">{{ node.label }}</span>
                        <q-btn v-if="node.isLeaf" @click="getDocumentDescription(node)" 
                            icon="visibility" color="primary" size="xs" flat round class="p-ml-2">
                                <q-popup-proxy anchor="bottom middle" self="top left">
                                    <div class="p-ml-2 p-mt-2" style="font-weight: bold; color: var(--q-primary);">Document Description</div>
                                    <q-separator class="p-my-2" />
                                    <el-scrollbar height="300px" class="p-p-3" style="width: 400px !important;">
                                    <div v-html="marked(docDescription)"></div>
                                    </el-scrollbar>
                                </q-popup-proxy>
                        </q-btn>
                        <q-btn v-if="node.isLeaf" @click="handleViewSourceDocument(node)"  icon="description" color="primary" size="xs" flat round Xclass="p-ml-0"></q-btn>
                        <q-btn v-if="showCategoryDescription(node)" @click="getCategoryDescription(node)" 
                            icon="visibility" color="primary" size="xs" flat round class="p-ml-2">
                            <q-popup-proxy anchor="bottom middle" self="top left">
                                <div class="p-ml-2 p-mt-2" style="font-weight: bold; color: var(--q-primary);">Category Description</div>
                                <q-separator class="p-my-2" />
                                <el-scrollbar height="300px" class="p-p-3" style="width: 400px !important;">
                                <div v-html="marked(catDescription)"></div>
                                </el-scrollbar>
                            </q-popup-proxy>
                        </q-btn>
                    </template>
                </el-tree>
                </el-scrollbar>
                <div v-else class="p-p-4 text-center text-grey-6">
                    Loading...
                </div>
            </el-main>
        </el-container>
    </q-card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useQuasar } from 'quasar'
import TooltipBtn from 'src/components/TooltipBtn.vue'
import { useStore } from 'src/stores/main-store';
import useTree from "src/composables/useTree.js";
import { marked } from 'marked';
import useNotify from 'src/composables/useNotify.js';

const $q = useQuasar()
const store = useStore()
const { generatePath } = useTree();
const { notifyProgress } = useNotify();

const scrollbarHeight = ref(100)
const treeRef = ref(null)

const defaultProps = {
  children: "children",
  label: "label",
};

const docDescription = ref('')
const catDescription = ref('')
const treeExpanded = ref(true)

onMounted(async () => {
  await store.getKBBuilderStatus();
});

// Watch for data changes and refresh the tree
watch(() => store.docTreeData, (newData) => {
  if (newData && treeRef.value) {
    // Force re-render of the tree
    treeRef.value.$forceUpdate?.()
  }
}, { deep: true })

async function getDocumentDescription(node) {
    let docpath = generateFilePath(node)
    // replace all '/' with '__':
    docpath = docpath.replace(/\//g, '__')
    docDescription.value = await store.getDocumentDescription(docpath)
}


async function getCategoryDescription(node) {
  const nodeCategoryPath = generatePath(node);
  catDescription.value =  await store.getCategoryDescription(nodeCategoryPath)
}

// generate the path of a node in the tree
function generateFilePath(node) {
    let path = []
    let currentNode = node
  
    while (currentNode.parent) {
        if (path.length == 0) {
            path.unshift(currentNode.data.file_name)
        }
        else {
            path.unshift(currentNode.label)
        }
      currentNode = currentNode.parent
    }
  
    path = path.join('/')
    // path = path.replace('/'+ROOT+'/', '') // remove the leading "/All Categories/" from the path
    // path = path.substring(1) // remove the leading '/' from the path
    return path;
  }

  function showCategoryDescription(node) {
    if (node.isLeaf) {
      return false
    }
    // check if all children are not leafs
    if (node.childNodes && node.childNodes.every(child => !child.isLeaf)) {
      return false
    }
    return true
  }

  async function handleViewSourceDocument(node) {
    notifyProgress('Loading source document ...', 3000);
    const docPath = generateFilePath(node)
    const result = await store.viewSourceDocument(docPath, true);
  
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

  function collapseExpandAll() {
    treeExpanded.value = !treeExpanded.value;
    if (treeExpanded.value) {
        expandAll();
    } else {
        collapseAll();
  }
}

function collapseAll() {
  if (treeRef.value) {
    const nodes = treeRef.value.store.nodesMap;
    Object.values(nodes).forEach((node) => {
      if (node.childNodes && node.childNodes.length > 0) {
        node.expanded = false;
      }
    });
  }
}

function expandAll() {
  if (treeRef.value) {
    const nodes = treeRef.value.store.nodesMap;
    Object.values(nodes).forEach((node) => {
      if (node.childNodes && node.childNodes.length > 0) {
        node.expanded = true;
      }
    });
  }
}

const kbBuilderStatus = computed(() => {
  if (store.kbBuilderStatus == 'Pending' || store.kbBuilderStatus == 'Working' || store.kbBuilderStatus == 'Error') {
    return "Processing";
  }
  return "Idle";
});

async function runKBBuilder() {
  await store.runKBBuilder();
  // store.kbBuilderStatus = 'Injesting documents ...';
}

async function showKBBuilderStatus() {
  // store.kbBuilderStatus = await store.getKBBuilderStatus();
  await store.getKBBuilderStatus();
}
</script>

<style scoped>
.fixed-toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background-color: white; /* or match your theme */
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

  :deep(.el-scrollbar) {
    padding-bottom: 0px !important;
    padding-top: 0px !important;
  }

  /* Force ellipsis truncation for tree node labels */
  :deep(.el-tree-node__content) {
    overflow: hidden !important;
  }

  :deep(.el-tree-node__label) {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 300px !important;
    display: inline-block !important;
  }
</style>