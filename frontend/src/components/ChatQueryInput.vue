<template>
    <div v-if="sessionStore.session.categories.length > 0" class="p-d-flex p-justify-content-between p-align-items-center">
      <q-input class="col col-grow p-pb-0"
        v-model="query"
        @keydown.enter.stop="submitUserQuery"
        color="primary"
        outlined
        rounded
        dense
        clearable
        autogrow
        type="textarea"
        label="Chat with the AI model"
        Xhint="hint"
        :disable="store.chatLoading"
        :loading="store.chatLoading"
      >
        <template v-slot:append>
          <q-btn
            @click="submitUserQuery"
            class="p-ml-1"
            :disabled="query == null || query == '' || store.chatLoading"
            size="sm"
            dense
            rounded
            color="primary"
            Xflat
            icon="arrow_upward"
          />
        </template>
      </q-input>

      <q-btn v-if="store.chatLoading" @click="abort()" icon="stop" 
        Xstyle="font-size: 1rem" class="p-ml-2" color="negative" size="sm" round Xdense Xflat Xoutline>
      </q-btn>
    </div>
  </template>
  
  <script setup>
    import { ref, nextTick } from 'vue'
    import { useStore } from 'src/stores/main-store';
    import { useSessionStore } from 'src/stores/session-store';
    import { useLlmStore } from 'src/stores/llm-store';
    import useUtils from 'src/composables/useUtils';
    const utils = useUtils()

    const llmStore = useLlmStore()
    
    const props = defineProps({
        
    })
    
    const store = useStore()
    const sessionStore = useSessionStore()
    
    const emit = defineEmits(['submit'])

    const query = ref('')
    
    async function submitUserQuery (event) {
        if (query.value == null || query.value == '') {
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
        emit('submit', query.value)

    }

    function clearQuery() {
        query.value = ''
    }

    function getQuery() {
        return query.value
    }

    function setQuery(value) {
      query.value = value
    }

    // Expose the clearQuery function to the parent component
    defineExpose({
      clearQuery, getQuery, setQuery
    })

    async function abort() {
      if (store.chatDismiss) {
        store.chatDismiss()
      }
      store.chatLoading = false;
      await llmStore.stopStream()
      store.chatLoading = false;

      llmStore.queries = [];
      llmStore.pdfImages = [];
      llmStore.pdfURLs = [];

      // Remove the last 2 messages from the chat 
      const selectedModel = sessionStore.session.model
      const messages = sessionStore.session.chats[selectedModel.value]
      messages.splice(messages.length - 2, 2)
      // Update the total tokens
      nextTick(() => {
          utils.updateTotalTokens();
        })
    }
  </script>


    