import { defineStore } from "pinia";
import { ref } from "vue";
import * as API from 'src/api/api.js';
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store'
// import useNotify from 'src/composables/useNotify';
import useUtils from 'src/composables/useUtils';
import { useCategoryStore } from 'src/stores/category-store';
import { useSearchStore } from 'src/stores/search-store';


export const useLlmStore = defineStore('llm', () => {
    // STORES:
    const store = useStore();
    const sessionStore = useSessionStore();
    const searchStore = useSearchStore();

    const utils = useUtils();

    // const { notify } = useNotify()

    // STATE:
    const queries = ref([]);
    const pdfImages = ref([]);
    const pdfURLs = ref([]);
  
    // ACTIONS:
    async function generateSummary(text) {
      store.explorerData.summary = ''
      store.explorerData.summary = await API.generateSummary(text);
    }

    // generate answer from LLM
    async function generateAnswer(query, text, excludeLLMKnowledgebase, promptKey) {
      excludeLLMKnowledgebase = excludeLLMKnowledgebase == 'Exclude'
        let result = await API.generateAnswer(query, text, excludeLLMKnowledgebase, promptKey, null);

        if (promptKey == 'QUESTIONS') {
          console.log('Original QUESTIONS result:', result);
          
          // Extract the answer from the JSON response if it's wrapped in an object
          if (typeof result === 'object' && result.answer) {
            result = result.answer;
          }
          
          // Replace <li> tags to add copy icons
          let replaced = result.replace(/<li>([^<]+)<\/li>/g, '<li>$1 <i class="material-icons copy-icon" style="cursor:pointer;font-size:16px;margin-left:8px;opacity:0.6">assignment</i></li>');
          
          // Also handle markdown-style * bullets within <ul> tags (for text search)
          replaced = replaced.replace(/\n\*([^*\n]+)/g, '<li>$1 <i class="material-icons copy-icon" style="cursor:pointer;font-size:16px;margin-left:8px;opacity:0.6">assignment</i></li>');
          console.log('After replacement:', replaced);
          console.log('Replacement worked:', replaced !== result);
          
          result = replaced;
        }
        return result;
      }

    async function generateSuggestedQueries(text) {
      if (text == '') {
        store.suggestedQueries = [];
        return;
      }
      store.suggestedQueries = await API.generateSugggestedQueries(text);
    }
   
    async function makeConcise(chunk) {
        if (chunk.concise_text) { // if concise text is already in the chunk
          chunk.text = chunk.concise_text // set to concise text
        } 
        else {
          const concise_text = await get_chunk_concise(chunk.documentID, chunk.id) // set concise text from DB
          if (concise_text == null) {
            // notify('Source document flagged - cannot make text concise!',
            //         { icon: 'error', iconColor: 'warning', textColor: 'warning' })
            return
          }
    
          chunk.concise_text = concise_text
          chunk.text = chunk.concise_text // set to concise text
        }
        chunk.status = 'C' // indicate concise
        // nextTick(() => {
          utils.updateTotalTokens();
        // })
      }

      async function restoreOriginal(documentID, firstChunkId, lastChunkId) {
        const chunks = await API.getExcerptChunks(documentID, firstChunkId, lastChunkId); // get original chunks from DB
        utils.updateTotalTokens();
        return chunks;
    }

    async function getExcerptConcise(excerptText) {
        const conciseText =  await API.getExcerptConcise(excerptText);
        // utils.updateTotalTokens();
        return conciseText;
    }

    // async function generateTitles(docTexts, docs) {
    //   return await API.generateTitles(docTexts, docs);
    // }

    async function generateTitle(docText, userQuery) {
      return await API.generateTitle(docText, userQuery);
    }


    async function chat(userQuery) {
        // Add the user's query message.
        const session = sessionStore.session;
        const messages = session.chats[session.model.value];
        const categoryStore = useCategoryStore();
        
        messages.push({ role: 'user', content: userQuery });
        const systemMessage = await utils.constructSystemMessage();

        if (utils.checkTokensExceed(systemMessage)) {
            return true; // return error if tokens exceed limit
        }

        // Get category labels and remove /General
        const categoryLabels = categoryStore.selectedCategories.map(cat => cat.label);
        const categories = searchStore._removeGeneral(categoryLabels);

        // Get citation metadata to send to backend
        const citationMetadata = await utils.getCitationMetadata();

        // Prepare the chat request payload.
        const chat_request = {
            model: session.model.value,
            messages: messages,
            max_tokens: session.maxTokens,
            temperature: session.temperature / 10,
            top_p: 0.7,
            top_k: 50,
            repetition_penalty: 1.1,
            categories: categories.join(',') || '' // Use processed category labels
        };

        queries.value = [];
        pdfImages.value = [];
        var isFirst = true;
        // Stream and accumulate the response chunks.
        for await (const msg of API.streamChat(chat_request, systemMessage, session.useTools, citationMetadata)) {
          if (msg.type == "chunk") {
            const chunk = msg.data;
            // if chunk is not just whitepace
            if (isFirst) {
              messages.push({ role: 'assistant', content: '' });
              isFirst = false;
            }
              // Append each chunk to the last message (assistant response).
            messages[messages.length - 1].content += chunk;
              // Optionally, you could trigger UI updates here if needed.
              
            // Scroll to bottom:
            // const messageArea = document.getElementById('message-area')
            // if (messageArea) {
            //   messageArea.scrollTop = messageArea.scrollHeight
            //     messageArea.scrollTop = messageArea.scrollHeight
            // }
          } 
          else if (msg.type == "query") {
            // if chunk is query
            const query = msg.data;
            queries.value.push(query);
          } 
          else if (msg.type == "read_page") {
            // parse location json
            console.log("received read page", msg.data);
            pdfImages.value.push(msg.data);
          }
          else if (msg.type == "load_pdf") {
            // parse location json
            console.log("received load pdf", msg.data);
            pdfURLs.value.push(msg.data);
          }
          else if (msg.type == "auth_error") {
            // Auth error notification already handled by API.streamChat
          } 
          else {
            // Error messages and other unknown types are logged here
            // Error notifications are handled by API.streamChat
            console.error("Unknown message type:", msg.type);
          }
        }
        
        return false; // indicate no error occurred
    }

    async function stopStream() {
      await API.stopStream();
    }

    async function getExcerptByHash(hash) {
      return await API.getExcerptByHash(hash);
    }

    return {
        generateSummary, generateAnswer, generateSuggestedQueries, getExcerptConcise, restoreOriginal, chat, stopStream, makeConcise, generateTitle, queries, pdfImages, pdfURLs, stopStream, getExcerptByHash
    }
});
