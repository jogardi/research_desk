<template>
  <div class="bg-content-area p-pt-4">
    <div ref="anchorElementRef" style="height: 1px;"></div>

    <el-scrollbar always :height="`${scrollbarHeight}px`" style="padding-left: 20px;">
        <!-- <div class="private-node" 
          style="padding-top: 5px; position: relative; height: 35px; border-left: 1px solid var(--private-node-tree-line-color);">
            <div 
              style="width: 20px; position: absolute; left: 0px; top: 20px; border-bottom: 1px solid var(--private-node-tree-line-color);">
            </div>
            <el-checkbox v-model="isPrivate" label="Private" size="large" @click="gotoPrivatePage()"  
              style="position: absolute; left:40px; top: 0px; font-weight: 700; font-size: var(--el-font-size-base); font-family: var(--el-font-family) !important" />
        </div> -->
        <el-tree
          ref="treeRef"
           class="bg-content-area" style="max-width: 100%;"
          :data="categoryStore.categoryTreeData"
          show-checkbox
          node-key="id"
          default-expand-all
          :indent="0"
          :expand-on-click-node="false"
          :check-on-click-node="false"
          @check-change="handleCheckChange"
          :props="defaultProps"
        >
        <template #default="{ node }">
          <span :data-testid="`category-${node.label.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '')}`">{{ node.label }}</span>
          <q-btn @click="getCategoryDescription(node)" v-if="node.isLeaf" icon="visibility" color="grey-6" size="xs" flat>
                  <q-popup-proxy anchor="bottom middle" self="top left">
                    <div class="p-ml-2 p-mt-2">Category Description</div>
                    <el-scrollbar height="300px" class="p-p-3" style="width: 400px !important;">
                      <div v-html="marked(catDescription)"></div>
                    </el-scrollbar>
                  </q-popup-proxy>
                </q-btn>
        </template>
      </el-tree>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from "src/stores/session-store";
import { useCategoryStore } from "src/stores/category-store";
import useTree from "src/composables/useTree.js";
import { useWindowSize, useElementBounding } from "@vueuse/core";
import { marked } from 'marked';

const store = useStore();
const sessionStore = useSessionStore();
const categoryStore = useCategoryStore();
const { generatePath, generateOptionsList } = useTree();

const treeRef = ref(null);
const isPrivate = ref(false);

const defaultProps = {
  children: "children",
  label: "label",
};

const catDescription = ref('')

const anchorElementRef = ref(null);
const { height: windowHeight } = useWindowSize();
const scrollbarHeight = ref(0); // Ref to hold calculated scrollbar height

// Watch window height
watch(windowHeight, () => {
  calculateScrollbarHeight();
});

// Watch for changes to sessionStore.session.categories
watch(() => sessionStore.session.categories, (newCategories) => {
  if (treeRef.value) {
    treeRef.value.setCheckedKeys(newCategories);
  }
}, { deep: true });

// Function to calculate scrollbar height dynamically
function calculateScrollbarHeight() {
  if (!anchorElementRef.value) { 
    return;
  }
  const bounding = useElementBounding(anchorElementRef.value); // Get reactive bounding values
  const height = bounding.height.value; // Access .value
  const top = bounding.top.value; // Access .value

  // Calculate remaining height
  const remainingHeight = windowHeight.value - top;

  scrollbarHeight.value = remainingHeight > 0 ? remainingHeight : 0; // Fallback to 600px if invalid
  scrollbarHeight.value -= 25; // Add 20px padding
}

onMounted(async () => {
  // Set checked keys (if applicable)
  if (treeRef.value) {
    treeRef.value.setCheckedKeys(sessionStore.session.categories);
  }

  // Update selected categories
  _updateSelectedCategories();

  generateOptionsList(treeRef.value) // generate the options list for the select
});

function handleCheckChange(node, isSelected, subtreeHasSelectedNodes) {
  if (!subtreeHasSelectedNodes) {
    const checkedKeys = treeRef.value.getCheckedKeys(true, false);
    sessionStore.session.categories = [...checkedKeys];
  }

  // Update selected categories and recalculate height
  _updateSelectedCategories();
}

function _updateSelectedCategories() {
  categoryStore.selectedCategories = [];
  if (treeRef.value && sessionStore.session.categories.length > 0) {
    sessionStore.session.categories.forEach((id) => {
      const node = treeRef.value.getNode(id);
      if (node) {
        const path = generatePath(node);
        categoryStore.selectedCategories.push({ id, label: path });
      }
    });
  }

  calculateScrollbarHeight();

}

function clearAll() {
  sessionStore.session.categories = [];
  categoryStore.selectedCategories = [];
  if (treeRef.value) {
    treeRef.value.setCheckedKeys([]);
  }
}

function updateCheckedCategories() {
  if (treeRef.value) {
    treeRef.value.setCheckedKeys(sessionStore.session.categories);
  }
}

function collapseExpandAll(treeExpanded) {
  if (treeExpanded) {
    collapseAll();
  } else {
    expandAll();
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

let nodeCategoryPath = '';

async function getCategoryDescription(node) {
  nodeCategoryPath = generatePath(node);
  catDescription.value =  await store.getCategoryDescription(nodeCategoryPath)
}

function gotoPrivatePage() {
  // navigateTo('/about-private-kb');
}

defineExpose({
  clearAll,
  updateCheckedCategories,
  collapseExpandAll,
});
</script>

<style>
.private-node .el-checkbox__inner {
  border: 2px solid var(--private-node-checkbox-border-color) !important;
}
.private-node .el-checkbox__label {
  color: var(--query-msg-color) !important;
}
</style>
