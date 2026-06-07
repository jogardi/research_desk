<template>
  <q-page id="category-selector" class="p-pt-2 p-px-3">
    <div class="page-flex-container">

      <!-- Category Tree -->
       <div class="toolbar p-d-flex p-justify-between p-align-items-center p-px-2 p-pt-0 p-pb-2" >
          <div class="Xsubtitle text-subtitle1 p-mt-0" 
          :class="store.initialized && categoryStore.selectedCategories.length == 0? 'text-negative' : ''" style="opacity: .8;">Select Knowledgebase Categories</div>
          <div class="p-d-flex p-justify-between p-align-items-end">
            <div>     
              <q-btn v-if="categoryView == 'browse'" Xflat @click="collapseExpandAll()" :label="expanded? 'Collapse' : 'Expand'" color="primary" flat no-caps size="md"  Xdense class="q-mr-sm" :icon="expanded? 'expand_less' : 'expand_more'" />
              <q-btn v-if="categoryView == 'browse'" Xflat @click="clearAll()" label="Clear" color="primary" flat no-caps size="md" Xdense class="q-mr-md" icon="cancel"/>
            </div>
            <q-btn-toggle
              v-model="categoryView"
              @update:model-value="onCategoryViewChange"
              Xpush
              no-caps
              Xrounded
              size="md"
              Xdense
              Xunelevated
              toggle-color="primary"
              color="grey-8"
              Xtext-color="primary"
              :options="[
                {label: 'Browse', value: 'browse'},
                {label: 'Search', value: 'search'}
              ]"
              style="opacity: .8;"
            />
          </div>
       </div>

       <!-- <q-separator spaced /> -->
      
       <div v-if="categoryView == 'browse'" class="bg-content-area">
        <div v-if="categoryStore.categoryTreeData.length > 0" Xclass="tree-container">          
            <category-tree ref="treeRef"></category-tree>
        </div>
      </div>

      <div v-if="categoryView == 'search'" class="bg-content-area p-pt-4  p-mt-3">
        <div class="p-pl-2 q-mb-sm" style="opacity: .8; font-size: .8rem">To search for categories, click in the input field past the last item and type a search query (notice the blinking edit indicator). Click the "X" icon to clear a category.</div>
        <category-select />
      </div>
    </div>
  </q-page>

  <q-drawer id="right-drawer" side="right" Xdark bordered class="q-pa-md"
      v-model="leftDrawerOpen"
      show-if-above
      :width="350"
    >
     <!-- Total tokens -->
      <!-- <total-tokens /> -->

      <!-- <div class="text-h6 text-grey-3">Element Plus Tree</div>
        <div class="q-mb-md">
          <el-button Xclass="dark" type="primary" Xdisabled>Hello</el-button>
        </div>
        <div v-if="categoryStore.categoryTreeData.length > 0">
          <el-scrollbar  always height="600" class="q-pa-md bg-body-color" style="zoom: 1.1;">
              <category-tree ref="treeRef"></category-tree>
          </el-scrollbar> 
        </div> -->
    </q-drawer>
</template>

<script setup>
  import { nextTick, ref, onMounted, onBeforeMount, computed } from 'vue'
  
  import { useQuasar } from 'quasar'
  import { useStore } from 'src/stores/main-store';
  import { useCategoryStore } from 'src/stores/category-store';
  import { useSessionStore } from 'src/stores/session-store';
  import TooltipBtn from 'src/components/TooltipBtn.vue'
  import useUtils from 'src/composables/useUtils';  
  import SelectedCategories from 'src/components/SelectedCategories.vue'
  import TotalTokens from 'src/components/TotalTokens.vue'
  import CategoryTree from 'src/components/category-selector/CategoryTree.vue'
  import CategorySelect from 'src/components/category-selector/CategorySelect.vue'
  
  // import ElTree from 'element-plus'
  // import ElButton from 'element-plus'


  const store = useStore()
  const categoryStore = useCategoryStore()
  const sessionStore = useSessionStore();
  const utils = useUtils()

  const $q = useQuasar()

  const leftDrawerOpen = ref(false)

  const query = ref('')

  const categoryView = ref('browse')

  // Category Tree
  const treeRef = ref(null)

  const selected = ref('')
  const expandedKeys = ref([ ])

  const categoryTree = ref(null) // ref('categoryTree') - to access the tree object
  const filter = ref('')
  const category = ref('')
  const isCategoryChecked = ref(false)

  const expanded = ref(true)

  onBeforeMount(async () => {
    console.log("*** CategorySelector.vue - onBeforeMount ***");  
  });

  function collapseExpandAll() {
      treeRef.value.collapseExpandAll(expanded.value);
      expanded.value = !expanded.value;
    }

  function clearAll() {
    treeRef.value.clearAll();
  }

  function onCategoryViewChange(value) {
    console.log("Category View changed to: ", value);
  }
</script>

<style scoped>
  .page-flex-container {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Make it fill the full viewport height */
  overflow: hidden; /* Prevent the page from scrolling */
}

.tree-container {
  flex-grow: 1; /* Allow this container to expand and fill available space */
  overflow-y: auto; /* Make only this container scrollable */
}

</style>