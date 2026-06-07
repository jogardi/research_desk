import { defineStore } from "pinia";
import { ref, watch } from "vue";
import * as API from 'src/api/api.js';
import { useModelStore } from 'src/stores/model-store';
import { useUserStore } from 'src/stores/user-store';
import useUtils from 'src/composables/useUtils';


export const useSessionStore = defineStore('session', () => {
    // STORES:
    const modelStore = useModelStore();
    const utils = useUtils();
    const userStore = useUserStore();
    // STATE:
    const sessionList = ref([]); // Holds list of all sessions

    const emptySession = { id: 0, categories: [], vectorDB: 'hnswlib', chunks: [], name: '', summary: '', messages: []};

    const session = ref(null); // The current session

    /* session object structure:
      session.categories - list of selected category IDs (in the current session)
    */

    // ACTIONS:
    async function initData() {
        sessionList.value = await API.loadSessionList();
        console.log("*** session-store - initData() called. kb_name: " + userStore.getUser().kb_name);
        if (sessionList.value.length == 0) {
            await addSession({ name: 'Your first session', description: 'Edit to rename and add your description'});
        }
  
        // session.value = await API.loadSession(sessionList.value[0].id);
        await loadSession(sessionList.value[0].id);
        // console.log("session-store - initData loaded session!");
    }

    async function loadSessionList() {
      sessionList.value = await API.loadSessionList();
      return sessionList.value;
    }

    async function loadSessionListForKbName(kb_name) {
      sessionList.value = await API.loadSessionListForKbName(kb_name);
      await loadSession(sessionList.value[0].id);
      return sessionList.value;
    }
      
    // load a session from server by id
    async function loadSession (sessionId) {
        const result = await API.loadSession(sessionId);
        if (result.isError) {
          return true; // error loading session
        }

        session.value = result.data;

        // load the models for the session
        const isError = await modelStore.loadModels();
        if (isError) {
          return true; // error loading models
        }

        modelStore.models.forEach(model => {
          if (!session.value.hasOwnProperty('chatsExcludeInclue')) { // if chatsExcludeInclue property not in session
            session.value.chatsExcludeInclue = {}; // add chatsExcludeInclue property
          }
          if (!session.value.chatsExcludeInclue.hasOwnProperty(model.value)) { // if model not in chatsExcludeInclue
            session.value.chatsExcludeInclue[model.value] = 'Include'; // add model to chatsExcludeInclue
          }
          // set active flag based on if the session chats has the conversation with the model
          model.active = session.value.chats.hasOwnProperty(model.value); 
        });

        // if no contextDocs property in session, add it:
        if (!session.value.contextDocs) {
          session.value.contextDocs = [];
        }
        // if no docs stashDocs in session, add it:
        if (!session.value.stashDocs) {
          session.value.stashDocs = [];
        }

        // if no explorer property in session, add it:
        if (!session.value.hasOwnProperty('explorer')) {
          session.value.explorer = {query: '', summary: '', answer: '', insights: '', concepts: '', questions: '', excludeInclude: 'Include'};
        }


        if (!session.value.hasOwnProperty('selectedLlmRoleId')) {
          session.value.selectedLlmRoleId = null;
        }

        if (!session.value.hasOwnProperty('useTools')) {
          session.value.useTools = {searchSemanticByDoc: false, readPage: false, loadPdf: false};

        }

        await utils.updateTotalTokens();

        // utils.updateSelectedCategoryPaths(); // update the selected categories

        watch(() => session.value.chunks, async (newChunks, oldChunks) => {
          await utils.updateTotalTokens();
        }, { deep: true })

        session.value.model.excludeInclude = 'Include'; // default to include
        // selectedCategoryPaths.value = await API.getCategoryPaths(session.value.categories, 'active');
        return false; // no error
      }
  
      async function addSession(session) {
        const data = await API.addSession(session);
        if (data) {
            sessionList.value.unshift(data.sessionItem);
            // session.value = data.sessionDetail;
            await loadSession(data.sessionItem.id); // make it the current active session
        }
      }

      async function saveSession() {
        const activeSessionItem = sessionList.value.find(sessionItem => sessionItem.id == session.value.id)
        session.value.name = activeSessionItem.name;
        
        const payload = {name: activeSessionItem.name, description: activeSessionItem.description, 'detail': session.value}

        const isError = await API.saveSession(session.value.id, payload);

        return isError;
      }
   
      // remove a session from server by id
      async function removeSession(sessionId) {
          const isDeleted = await API.removeSession(sessionId);
          if (!isDeleted) return false;
          sessionList.value = sessionList.value.filter(s => s.id !== sessionId);
          if (sessionList.value.length == 0) {
            await addSession({ name: 'Your first session', description: 'Edit and rename to add your description'});
          }
          else {
            await loadSession(sessionList.value[0].id) // load first session in list
          }
          return true;
      }

      async function forkSession(sessionId, session) {
        const data = await API.forkSession(sessionId, session);
        if (data) {
            sessionList.value.unshift(data.sessionItem);
            await loadSession(data.sessionItem.id); // make it the current active session
        }
      }

    // GETTERS:
    // Computed properties or getters can be added here if necessary

    // RETURN STATE, ACTIONS, AND GETTERS:
    return { 
        sessionList, session, loadSessionList, loadSessionListForKbName,
        initData, loadSession, addSession, saveSession, removeSession, forkSession
    };
});
