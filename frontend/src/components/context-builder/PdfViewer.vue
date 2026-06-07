<template>
  <div class="pdf-viewer bg-body-color">
    <!-- Make the header fixed -->
    <q-toolbar class="pdf-header p-d-flex p-justify-content-between p-align-items-center text-positive">
      <q-toolbar-title v-if="!isLoading">Source File Viewer</q-toolbar-title>
      <span>
        <span v-if="!isLoading" class="p-mr-3">
          <!-- <q-icon name="description" color="info" size="xs" class="p-mr-3">
            <tooltip >{{docPath}}</tooltip>
            </q-icon> -->
            <tooltip-btn @click="handleViewSourceDocument()" :tooltip="docPath" icon="description" color="info" flat size="xs" class="p-mr-3"></tooltip-btn>
          <span class="hilite-sentence p-mr-1" style="font-weight: bold;">Focus</span>
          <span class="p-mr-1">|</span>
          <span class="text-green-8" style="font-weight: bold;">Contextual</span>
        </span>
        <!-- <span v-if="isLoading" class="text-info" style="font-size: 1.1rem;">
          <q-spinner-audio thickness="10" size="sm" />
          Loading Source File ...
        </span> -->
       
        <q-btn @click="hidePdfViewer()" dense flat size="sm" color="primary" icon="close" data-testid="pdf-viewer-close-button" />
      </span>
    </q-toolbar>

    <div v-if="store.pdfViewerData.docType == 'CSV'" class="p-pl-3 text-blue-4">CSV File - please download manually.</div>

    <div class="pdf-container" v-if="!isLoading">
      <iframe  @load="iframeLoaded" ref="iframeRef"
        v-if="pdfUrl && !isLoading"
        :src="pdfUrl" 
        class="pdf-iframe"
        frameborder="0"
      ></iframe>
    </div>
    <div class="p-d-flex p-justify-center p-align-center Xp-mt-2 bg-body-color" v-if="isLoading" 
      style="height: 100%; width: 100%;">
      <q-spinner-audio thickness="10" size="sm" color="info" />
      <span class="p-ml-2">Loading Source File ...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useStore } from 'src/stores/main-store';
import { Config } from 'src/config.js';
import TooltipBtn from 'src/components/TooltipBtn.vue'
import useNotify from 'src/composables/useNotify.js';

// Store and reactive refs
const store = useStore();
const { notifyProgress } = useNotify();
const documentUrl = ref('');
const pdfUrl = ref('');
const isLoading = ref(false);
const iframeRef = ref(null);

const docPath = ref('');
const baseUrl = ref('');

function iframeLoaded() {
  // add data-testid as 'pdfIframeLoaded' to the iframe
  iframeRef.value.setAttribute('data-testid', 'pdfIframeLoaded');
}

// Calculate vertical offset from highlights data
function calcVerticalOffset(highlights) {
  const normalizedOffset = highlights && 
                           highlights.length > 0 && 
                           highlights[0].y !== undefined
                           ? highlights[0].y : 0;
  // Convert normalized coordinate (0-1) to PDF points
  // Use conservative scaling to ensure highlight stays visible
  const pageHeight = 750; // Conservative estimate, smaller than both US Letter (792) and A4 (842)
  // Subtract some padding to scroll slightly above the highlight for better visibility
  const padding = 50; // Points above the highlight
  return Math.max(0, Math.round(normalizedOffset * pageHeight) - padding);
}

// Update document URL and viewer URL
async function updateUrls() {
  try {
    isLoading.value = true;
    
    // First, get the document path
    let path = '';
    if (store.pdfViewerData.documentPath) {
      path = store.pdfViewerData.documentPath;
      // Check if path is a string before using startsWith
      if (typeof path === 'string' && path.startsWith("Document: ")) {
        path = path.substring("Document: ".length);
      }
    } 
    else if (store.pdfViewerData.documentId) {
      try {
        const result = await store.getDocumentInfo(store.pdfViewerData.documentId);
        if (result && result.category && result.filename) {
          path = result.category + '/' + result.filename;
        } else {
          console.error("Invalid document info result:", result);
        }
      } catch (error) {
        console.error("Error loading document info:", error);
      }
    }
   
    // Update the document URL
    documentUrl.value = path || '';
    
    // Now create the direct PDF URL
    if (documentUrl.value) {
      baseUrl.value = documentUrl.value;
      
      // Check if we need to add highlighting
      // Only highlight if documentPath is NOT directly provided (meaning we're using documentId)
      const shouldHighlight = !store.pdfViewerData.documentPath && store.pdfViewerData.highlights && 
                                // store.pdfViewerData.highlights.x && store.pdfViewerData.highlights.y && 
                                // store.pdfViewerData.highlights.width && store.pdfViewerData.highlights.height &&
                                store.pdfViewerData.pageNumber;

      if (shouldHighlight && store.pdfViewerData.docType != 'PPT' && store.pdfViewerData.docType != 'CSV') { // if highlighting is needed
        try {
          // Create default highlight if not provided
          const highlights = store.pdfViewerData.highlights;

          // Call the store method to get highlighted PDF
          const result = await store.getHighlightedPdf(baseUrl.value, store.pdfViewerData.pageNumber, highlights);
          
          if (!result.isError && result.data) { // if highlighting is successful
            // Get the response as a blob
            const blob = result.data;
            
            // Create a blob URL for the highlighted PDF
            const blobUrl = URL.createObjectURL(blob);
            
            // Add page fragment to the blob URL to navigate to the correct page
            const verticalOffset = calcVerticalOffset(store.pdfViewerData.highlights);
            console.log("DEBUG - calculated verticalOffset:", verticalOffset);
            pdfUrl.value = blobUrl + `#page=${store.pdfViewerData.pageNumber}&zoom=100,0,${verticalOffset}&navpanes=0&view=FitH`; // + '&toolbar=0&navpanes=0&scrollbar=0';
            
            console.log("Created highlighted PDF URL with page fragment:", pdfUrl.value);
          } 
          else {
            throw new Error("Failed to get highlighted PDF");
          }
        } 
        catch (error) { // if highlighting fails, fall back to the original PDF
          console.error("Error highlighting PDF:", error);
          // Fall back to the original PDF with page fragment
          try {
            const result = await store.viewSourceDocument(baseUrl.value, true);
            if (!result.isError && result.data) {
              const blob = result.data;
              const blobUrl = URL.createObjectURL(blob);
              const verticalOffset = calcVerticalOffset(store.pdfViewerData.highlights);
              console.log("DEBUG - calculated verticalOffset (highlighting failed):", verticalOffset);
              const pageFragment = store.pdfViewerData.pageNumber 
                ? `#page=${store.pdfViewerData.pageNumber}&zoom=100,0,${verticalOffset}&toolbar=0&navpanes=0&scrollbar=0&view=FitH` 
                : '#toolbar=0&navpanes=0&scrollbar=0';
              pdfUrl.value = blobUrl + pageFragment;
            }
          } catch (fallbackError) {
            console.error("Error in fallback source file loading:", fallbackError);
          }
        }
      } 
      else {
        // Just use the original PDF with page fragment - no highlighting
        try {
          const result = await store.viewSourceDocument(baseUrl.value, true);
          if (!result.isError && result.data) {
            // Get the response as a blob
            const blob = result.data;
              
              // Create a blob URL for the highlighted PDF
              const blobUrl = URL.createObjectURL(blob);

            const verticalOffset = calcVerticalOffset(store.pdfViewerData.highlights);
            const pageFragment = store.pdfViewerData.pageNumber 
              ? `#page=${store.pdfViewerData.pageNumber}&zoom=100,0,${verticalOffset}&toolbar=1&navpanes=0&scrollbar=0&view=FitH` 
              : '#toolbar=1&navpanes=0&scrollbar=0';
            // pdfUrl.value = `https://corsproxy.io/?key=e373b745&url=${encodeURIComponent(baseUrl.value)}${pageFragment}`;
            // pdfUrl.value = `${Config.API_SERVER}/doc/send/filepath?filepath=${baseUrl.value}${pageFragment}`
            pdfUrl.value = blobUrl + pageFragment; // + '&toolbar=0&navpanes=0&scrollbar=0'; 
          }
          else {
            throw new Error("Failed to get source document");
          }
        }
        catch (error) {
          console.error("Error viewing source document:", error);
        }
      }
      
      console.log("Updated source file URL:", pdfUrl.value, "Page:", store.pdfViewerData.pageNumber);
    } 
    else {
      pdfUrl.value = '';
    }

    docPath.value = documentUrl.value;

    isLoading.value = false;
  } 
  catch (error) {
    console.error("Error updating URLs:", error);
    documentUrl.value = '';
    pdfUrl.value = '';
    isLoading.value = false;
  }
}

// Watch for changes in PDF viewer data
watch([() => store.pdfViewerData, () => store.pdfViewerData.documentPath, () => store.pdfViewerData.documentId], () => {
  updateUrls();
});

// Watch for changes in page number or highlight
watch([() => store.pdfViewerData.pageNumber, () => store.pdfViewerData.highlight], () => {
  if (documentUrl.value) {
    updateUrls();
  }
});

// Initial setup
onMounted(async () => {
  await updateUrls();
});

onUnmounted(() => {
  // Clean up any blob URLs to prevent memory leaks
  if (pdfUrl.value && pdfUrl.value.startsWith('blob:')) {
    const url = pdfUrl.value.split('#')[0]; // Remove fragment before revoking
    URL.revokeObjectURL(url);
  }
  store.pdfViewerData.show = false;
});

function hidePdfViewer() {
  // Clean up any blob URLs to prevent memory leaks
  if (pdfUrl.value && pdfUrl.value.startsWith('blob:')) {
    const url = pdfUrl.value.split('#')[0]; // Remove fragment before revoking
    URL.revokeObjectURL(url);
  }
  store.pdfViewerData.show = false;
}

async function handleViewSourceDocument() {
  notifyProgress('Loading source document ...', 3000);
  const result = await store.viewSourceDocument(baseUrl.value, true);
  
  if (!result.isError && result.data) {
    // Create a temporary URL for the blob
    const url = window.URL.createObjectURL(result.data);
    
    // Open in new tab
    window.open(url, '_blank');
    
    // Clean up the temporary URL after a short delay
    setTimeout(() => window.URL.revokeObjectURL(url), 1000);
  }
  // Error handling is already done in the API layer via _notifyException
}
</script>

<style scoped>
.pdf-viewer {
  position: relative;
  /* position: absolute;
  top: 0;
  left: 0; */
  width: 100%;
  height: 100%;
  /* background-color: white; */
  display: flex;
  flex-direction: column;
  z-index: 100;
  border: 1px solid #666;
}

/* .pdf-header {
  height: 50px;
  min-height: 50px;
  flex-shrink: 0;
} */



.pdf-container {
  flex-grow: 1;
  /* height: calc(100% - 50px); */
  position: relative;
  overflow: hidden;
  background-color: #f5f5f5;
}

:deep(.body--dark) .pdf-container {
  background-color: #1e1e1e;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
