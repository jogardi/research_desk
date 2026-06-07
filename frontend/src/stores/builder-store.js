import { defineStore } from "pinia";
import { ref } from "vue";
import * as API from 'src/api/api.js';

export const useBuilderStore = defineStore('builder', () => {
    // STATE:
    const builderCategoryPaths = ref([]);
    const builderSelectedCategoryIDs = ref([]);

    // ACTIONS:
    // Load all categories suitable for the builder
    async function loadBuilderCategories() {
        const data = await API.loadCategories('all');
        return data.categories;
      }

    // Generates databases for the given builder category IDs
    async function generateDatabasesForBuilder() {
        return await API.generate_databases(builderSelectedCategoryIDs.value);
    }

    // RETURN STATE, ACTIONS, AND GETTERS:
    return { 
        builderCategoryPaths, 
        builderSelectedCategoryIDs,
        loadBuilderCategories,
        generateDatabasesForBuilder
    };
});
