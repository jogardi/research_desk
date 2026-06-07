<template>
    <div id="selected-categories" Xmouseenter="store.showNavbar = true" Xmouseleave="store.showNavbar = false">
      <div class="p-pl-2">
        <div v-if="categoryStore.selectedCategories && categoryStore.selectedCategories.length > 0">
          <div v-if="hasOverflow" class="p-d-flex p-align-items-center">
            <div class="chips-display">
              <!-- Show visible chips -->
              <div v-for="category in visibleCategories" :key="category">
                <q-chip 
                  Xremove="log(category)" 
                  Xremovable 
                  size=".8rem" 
                  square
                  color="selected-categories-color" 
                  text-color="selected-categories-color"
                >
                  {{ splitCategoryPath(category.label).folder }}<b class="text-info" style="font-weight: 675;">{{ splitCategoryPath(category.label).name }}</b>
                </q-chip>
              </div>
              
              <!-- More button to open dialog -->
              <q-btn 
                flat 
                dense 
                round 
                icon="more_horiz" 
                size="md" 
                style="opacity: .5;"
                class="q-ml-xs"
                @click="isExpanded = true"
              />
            </div>
            
            <!-- Dialog with all categories -->
            <el-dialog v-model="isExpanded" :top="dlgTop" :width="dlgWidth" Xshow-close="false"
              class="dialog-body Xp-pt-0" style="border-radius: 10px;">
              <header class="p-d-flex p-justify-content-center p-pb-2 p-px-3">
                <div class="text-subtitle1 Xtext-weight-medium" style="opacity: 0.8;">All Selected Categories</div>
              </header>
              <div class="p-px-2 p-pb-3">
                <div class="chips-display">
                  <!-- Show ALL categories in the dialog -->
                  <div v-for="category in categoryStore.selectedCategories" :key="category">
                    <q-chip 
                      Xremove="log(category)" 
                      Xremovable 
                      size=".8rem" 
                      square
                      color="selected-categories-color" 
                      text-color="selected-categories-color"
                    >
                      {{ splitCategoryPath(category.label).folder }}<b class="text-info" style="font-weight: 675;">{{ splitCategoryPath(category.label).name }}</b>
                    </q-chip>
                  </div>
                </div>
              </div>
            </el-dialog>
          </div>
          <!-- Simple display when no overflow -->
          <div v-else class="chips-display">
            <div v-for="category in categoryStore.selectedCategories" :key="category">
              <q-chip 
                Xremove="log(category)" 
                Xremovable 
                size=".8rem" 
                square
                color="selected-categories-color" 
                text-color="selected-categories-color"
              >
                {{ splitCategoryPath(category.label).folder }}<b class="text-info" style="font-weight: 675;">{{ splitCategoryPath(category.label).name }}</b>
              </q-chip>
            </div>
          </div>
          
          <!-- Hidden measurement container -->
          <div ref="measureContainer" class="measure-container">
            <div v-for="(category, index) in categoryStore.selectedCategories" :key="category" :ref="el => setChipRef(el, index)">
              <q-chip 
                size=".8rem" 
                square
                color="selected-categories-color" 
                text-color="selected-categories-color"
              >
                {{ splitCategoryPath(category.label).folder }}<b class="text-info" style="font-weight: 675;">{{ splitCategoryPath(category.label).name }}</b>
              </q-chip>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import { useStore } from 'src/stores/main-store';
import { useCategoryStore } from 'src/stores/category-store';

  const store = useStore();
  const categoryStore = useCategoryStore();
  
  const isExpanded = ref(false);
  const measureContainer = ref(null);
  const chipRefs = ref([]);
  const visibleCount = ref(0);
  const hasOverflow = ref(false);

  const props = defineProps({
    // noneSelectedMessage: {
    //   type: String
    // },
    iconName: {
      type: String,
      default: 'error_outline'
    },
    iconSize: {
      type: String,
      default: 'md'
    }
  });

  watch(
    () => store.layoutSelectedTab,
    () => {
      // collapse the chips if the tab is changed
      console.log('Tab changed, collapsing chips. Current isExpanded:', isExpanded.value);
      isExpanded.value = false;
      console.log('Set isExpanded to:', isExpanded.value);
      nextTick(measureChips);
    }
  );

  const visibleCategories = computed(() => {
    return categoryStore.selectedCategories?.slice(0, visibleCount.value) || [];
  });

  const hiddenCategories = computed(() => {
    return categoryStore.selectedCategories?.slice(visibleCount.value) || [];
  });

  function setChipRef(el, index) {
    if (el) {
      chipRefs.value[index] = el;
    }
  }

  function measureChips() {
    if (!measureContainer.value || !categoryStore.selectedCategories?.length) {
      hasOverflow.value = false;
      visibleCount.value = categoryStore.selectedCategories?.length || 0;
      return;
    }

    nextTick(() => {
      const container = measureContainer.value;
      if (!container.parentElement) return;
      
      const containerWidth = container.parentElement.clientWidth;
      let totalWidth = 0;
      let count = 0;
      
      // Account for more indicator and chevron space (approximately 40px)
      const reservedSpace = 40;
      const availableWidth = containerWidth - reservedSpace;

      for (let i = 0; i < chipRefs.value.length; i++) {
        const chipEl = chipRefs.value[i];
        if (chipEl) {
          const chipWidth = chipEl.offsetWidth + 4; // +4 for gap
          
          if (totalWidth + chipWidth <= availableWidth) {
            totalWidth += chipWidth;
            count++;
          } else {
            break;
          }
        }
      }

      // Ensure we show at least 1 chip, but if all fit, show all
      if (count === 0 && categoryStore.selectedCategories.length > 0) {
        count = 1; // Show at least one chip
      } else if (count === categoryStore.selectedCategories.length) {
        // All chips fit, no overflow
        hasOverflow.value = false;
        visibleCount.value = count;
        return;
      }

      visibleCount.value = count;
      hasOverflow.value = count < categoryStore.selectedCategories.length;
    });
  }

  function splitCategoryPath(path) {
  const lastSlashPos = path.lastIndexOf('/')
  if (lastSlashPos == -1) {
    return {
      folder: '',
      name: path
    }
  }
  let folder = path.substring(0, lastSlashPos)
  if (folder != '') {
    folder += '/'
  }
  return {
    folder: folder,
    name: path.substring(lastSlashPos + 1)
  }
}

  function log(path) {
    console.log(path);
  }

  // Watch for changes in selected categories
  watch(
    () => categoryStore.selectedCategories,
    () => {
      nextTick(measureChips);
    },
    { deep: true, immediate: true }
  );

  onMounted(() => {
    measureChips();
    // Re-measure on window resize
    window.addEventListener('resize', measureChips);
  });

  const dlgWidth = computed(() => {
    const selectedCategoriesEl = document.getElementById('selected-categories');
    if (selectedCategoriesEl) {
      return selectedCategoriesEl.offsetWidth * 0.85;
    }
    return 0;
  });

  const dlgTop = computed(() => {
    const el = document.getElementById('selected-categories')
    // get element by q-chip class:
    if (el) {
      const chip = el.querySelector('.q-chip');
      return (el.offsetTop + chip.offsetHeight + 10) + 'px';
    }
    return '0px';
  });
  </script>
  
  <style scoped>
  .chips-display {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
  }
  
  .more-indicator {
    display: flex;
    align-items: center;
    padding: 0 4px;
  }
  
  .measure-container {
    position: absolute;
    visibility: hidden;
    top: -9999px;
    display: flex;
    gap: 4px;
    white-space: nowrap;
  }
  </style>
  