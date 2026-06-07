import { defineStore } from "pinia";
import { ref, watch } from "vue";
import * as API from 'src/api/api.js';

export const useCategoryStore = defineStore('category', () => {
    // STATE:
    // Tree data
    const categoryTreeData = ref([]); // the category tree returned from the API call
    const categoryIDs = ref([]);      // the category IDs returned from the API call
    // Select options data
    const categoryListData = ref([]); // array of { id: id, label: path} objects

    // Selected/checked categories
    const selectedCategories = ref([]) // the tree-checked and list-selected category objects: array of { id: id, label: path } objects 

    // ACTIONS:
    async function initData(selectedCategoriesIDs) {
        const data = await API.loadCategories('active');
        categoryTreeData.value = data.categories;
        categoryIDs.value = data.categoryIDs;
        
        if (!selectedCategoriesIDs || selectedCategoriesIDs.length === 0) {
            return;
        }
        // populate selectedCategories
        selectedCategories.value = [];
      
        function traverse(node, path) {
          const currentPath = [...path, node.label];
          if (selectedCategoriesIDs.includes(node.id)) {
            selectedCategories.value.push({ id: node.id, label: currentPath.join('/') });
          }
          if (node.children) {
            node.children.forEach(child => traverse(child, currentPath));
          }
        }
      
        data.categories.forEach(rootNode => traverse(rootNode, []))
      }

    // RETURN STATE, ACTIONS, AND GETTERS:
    return { 
        categoryTreeData, categoryIDs, categoryListData, selectedCategories,
        initData
    };
});
