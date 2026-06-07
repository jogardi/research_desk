import { defineStore } from "pinia";
import { ref } from "vue";
import * as API from 'src/api/api.js';

export const useModelStore = defineStore('model', () => {

    // STATE:
    const defaultModel = ref(null);
    const models = ref([]);

    // ACTIONS:
    async function loadModels() {
      if (models.value.length == 0) { // if models have not been loaded yet
        const result = await API.loadModels();

        if (result.isError) {
          return true; // error loading models
        }

        models.value = result.data;
        defaultModel.value = models.value[0];
        return false; // success
      }
    }

    return {
      defaultModel,
      models,
      loadModels
    };
    
});
