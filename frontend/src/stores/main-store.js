import { defineStore } from "pinia";
import { ref } from "vue";
import * as API from 'src/api/api.js';
import { useUserStore } from 'src/stores/user-store';
import { useCategoryStore } from 'src/stores/category-store';
import { useSessionStore } from 'src/stores/session-store';
import { useRouter } from 'vue-router';
import useUtils from 'src/composables/useUtils'; // import the useUtils composable

export const useStore = defineStore('main', () => {
    // STORES:
    const categoryStore = useCategoryStore();
    const sessionStore = useSessionStore();
    const userStore = useUserStore();
    const utils = useUtils(); // use the useUtils composable

    const router = useRouter();


    // STATE:
    const initialized = ref(false); 
    const showNavbar = ref(true);
    const kbBuilderStatus = ref(null);
    const pdfViewerData = ref({
      show: false,
      documentPath: null,
      documentId: null,
      // sentenceId: null,
      pageNumber: null,
      highlights: null,
    });

    const canViewDocuments = ref(['.pdf', '.txt', '.mp4',  '.mp3', '.webm', '.wav', '.ogg', 'jpg', '.jpeg', '.png', '.gif', '.svg', 'bmp', '.webp', '.apng', '.html', '.htm' ]);

    // doc tree data
    const docTreeData = ref(null);
    const docIDs = ref(null);
  
    const layoutSelectedTab = ref('category-selector') // the selected tab in the layout top bar
    const contextBuilderSelectedTab = ref('context') // the selected tab in the context builder page top bar

    const totalTokens = ref(0)
    
    const chatLoading = ref(false)
    const chatDismiss = ref(null)
    const semanticSearchLoading = ref(false)
    const textSearchLoading = ref(false)
    const explorerLoading = ref(false)
    const explorerLoadingAsk = ref(false)

    const llmRoles = ref([])

    const excludeInclude = ref('Include')

    const suggestedQueries = ref([]);

    // explorer data:
    const explorerSemanticSearchData = ref({
      docs: null,
      summary: '',
      insights: '',
      concepts: '',
      querySuggestions: [],
      query: '',
      answer: '',
      questions: [],
      excludeInclude: 'Include'
    });

    const explorerTextSearchData = ref({
      docs: null,
      summary: '',
      insights: '',
      concepts: '',
      querySuggestions: [],
      query: '',
      answer: '',
      questions: [],
      excludeInclude: 'Include'
    });

    const explorerData = ref({
      query: '',
      querySuggestions: [],
      summary: '',
      insights: '',
      concepts: '',
      answer: '',
      questions: [],
      excludeInclude: 'Include',
      docs: null
    }); // the data for the explorer page: context, semantic or text search data
    const currentExplorerSource = ref('context'); // context, semantic-search or text-search

    const fromChatQuery = ref(false);

    // INITIALIZATION:

    console.log("*** main-store - created!");

    // initialize(); // initialize the store

    // initialize the store
    async function initialize() {
      console.log("*** main-store - initialize() called ...");

      const isLoggedin = localStorage.getItem('_id_');
      if (!isLoggedin) {
        console.log("   *** main-store - navigate to login page ...");
        router.replace('/login');
        return;
      }
      
      console.log("   *** main-store - user is logged in ...");
      
      await initData(); // load the needed data from the server
    }

    // ACTIONS:
    // load the needed data from the server
    async function initData() {
      console.log("*** main-store - initData() called ...");
      if (initialized.value) { // if already initialized,
        console.log(" *** main-store - initData already initialized, skipping ...");
        return;
      }

      console.log("   *** main-store - initData loading data ...");
      await sessionStore.initData();
      await categoryStore.initData(sessionStore.session.categories);

      llmRoles.value = await API.loadLlmRoleList();

      initialized.value = true;

      // utils.updateSelectedCategoryPaths(); // update the selected categories

      console.log("   *** main-store - initData loaded: session list, first session  and active categories!");

      // selectedCategoryPaths.value = await API.getCategoryPaths(session.value.categories, 'active');
    }

    function getSelectedLlmRole() {
      if (sessionStore.session.selectedLlmRoleId == null) {
        console.log("No Selected Prompt!")
        return null;
      }
      return llmRoles.value.find(prompt => prompt.id == sessionStore.session.selectedLlmRoleId);
    }

    async function getDocumentInfo(documentID) {
      return await API.getDocumentInfo(documentID);
    }

    async function getDocumentDescription(documentID) {
      return await API.getDocumentDescription(documentID);
    }

    async function getCategoryDescription(categoryPath) {
      categoryPath = categoryPath.replace('/General', '') // remove '/General' from the path
      return await API.getCategoryDescription(categoryPath);
    }

    async function showPdfViewerByCitationHash(citationHash) {
      try {
        const result = await API.getExcerptByHash(citationHash);
        
        const { chunks, document_id, docType } = result.data;
        
        // Set up PDF viewer
        pdfViewerData.value.show = true;
        pdfViewerData.value.documentPath = null;
        pdfViewerData.value.documentId = document_id;
        pdfViewerData.value.docType = docType;
        pdfViewerData.value.pageNumber = chunks[0].region?.page_number || 1;
        pdfViewerData.value.highlights = chunks
          .filter(chunk => chunk.region)
          .map(chunk => ({
            focus: true,
            page_number: chunk.region.page_number,
            x: chunk.region.horizontal_position,
            y: chunk.region.vertical_position,
            width: chunk.region.width,
            height: chunk.region.height
          }));
        
        console.log('PDF viewer set up for citation:', citationHash, 'with', chunks.length, 'chunks');
        
      } catch (error) {
        console.error('Error showing PDF for citation:', citationHash, error);
      }
    }

    async function showPdfViewer(excerpt, doc) {
      pdfViewerData.value.show = true
      pdfViewerData.value.documentPath = null
      pdfViewerData.value.documentId = doc.documentID
      pdfViewerData.value.pageNumber = doc.chunks[excerpt[0]].region.page_number
      pdfViewerData.value.docType = doc.docType;

      pdfViewerData.value.highlights = []

      // const chunk = doc.chunks[excerpt[0]];
      for (let index = excerpt[0]; index <= excerpt[1]; index++) {
        const chunk = doc.chunks[index]
        // pdfViewerData.value.sentenceId = chunk.id
        console.log("chunk score: " + chunk.score)
        pdfViewerData.value.highlights.push({ focus: chunk.score != 2, page_number: chunk.region.page_number, 
              x: chunk.region.horizontal_position, y: chunk.region.vertical_position, width: chunk.region.width, height: chunk.region.height })
      }
    }


    async function showPdfViewerByPath(documentPath, pageNumber) {
      pdfViewerData.value.show = true
      pdfViewerData.value.documentPath = documentPath
      pdfViewerData.value.pageNumber = pageNumber
    }

    async function viewSourceDocument(documentIdOrPath, isPath=false) {
      const result = await API.viewSourceDocument(documentIdOrPath, isPath);
      return result; // Return the result with blob data for the component to handle
    }

    async function getHighlightedPdf(baseUrl, pageNumber, highlights) {
      if (baseUrl.includes('/General/')) {
        baseUrl = baseUrl.replace('/General/', '/');
      }
      const result = await API.highlightPdf(baseUrl, pageNumber, highlights);
      return result; // Return the result with blob data for the component to handle
    }

    async function loadDocTreeData() {
      // if (docTreeData.value && docTreeData.value.length > 0)
      //   return;

      const data = await API.loadCategories('documents');
        docTreeData.value = data.categories;
        docIDs.value = data.categoryIDs;
    }


    // run the KB builder
    async function runKBBuilder() {
      kbBuilderStatus.value = await API.runKBBuilder();
      return result;
    }

    // get the status of the KB builder
    async function getKBBuilderStatus() {
      kbBuilderStatus.value = await API.getKBBuilderStatus();
    }

    function canViewDocument(doc) {
      return canViewDocuments.value.some(ext => doc.documentName.toLowerCase().endsWith(ext));
    }

    async function downloadPdf(reportData) {
      try {
        const result = await API.downloadPdf(reportData);
        return result;
      } catch (error) {
        console.error('Error downloading PDF:', error);
        return { data: null, isError: true };
      }
    }

    async function addLlmRole(llmRole) {
      const result = await API.addLlmRole({ role: llmRole });
      llmRoles.value.unshift(result);
      sessionStore.session.selectedLlmRoleId = result.id;
    }

    async function saveLlmRole(llmRole) {
      await API.saveLlmRole(llmRole);
    }

    async function removeLlmRole(llmRoleId) {
      await API.removeLlmRole(llmRoleId);
      llmRoles.value = llmRoles.value.filter(role => role.id != llmRoleId);
      if (sessionStore.session.selectedLlmRoleId == llmRoleId) {        
        sessionStore.session.selectedLlmRoleId = null;
      }
    }

    return {
      initialize, initialized,
      getDocumentInfo, getDocumentDescription, getCategoryDescription, getSelectedLlmRole,
      llmRoles, layoutSelectedTab, contextBuilderSelectedTab, suggestedQueries, 
      chatDismiss, chatLoading, semanticSearchLoading, textSearchLoading, explorerLoading, explorerLoadingAsk,
      totalTokens, excludeInclude, pdfViewerData, showPdfViewer, showPdfViewerByCitationHash, showPdfViewerByPath, viewSourceDocument, getHighlightedPdf, loadDocTreeData,
      docTreeData, docIDs, explorerData, explorerSemanticSearchData, explorerTextSearchData, currentExplorerSource, showNavbar, canViewDocument, downloadPdf,
      addLlmRole, saveLlmRole, removeLlmRole, fromChatQuery, kbBuilderStatus, runKBBuilder, getKBBuilderStatus
    };
});
