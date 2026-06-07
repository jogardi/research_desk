<template>
  <div class="pdf-viewer">
    <!-- Make the header fixed -->
    <q-toolbar class="pdf-header p-d-flex p-justify-content-between p-align-items-center text-positive  bg-body-color">
      <q-toolbar-title>PDF Viewer</q-toolbar-title>
      <!-- <div class="title Xtext-h6 p-px-0">PDF Viewer</div> -->
      <q-btn @click="hidePdfViewer()" dense flat size="sm" color="primary" icon="close" />
    </q-toolbar>
    <div ref="container" class="pdf-container">
      <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
      <div  id="region_highlight"
        class="highlight"
        :style="highlightStyle"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, nextTick } from "vue";
import { useStore } from 'src/stores/main-store';
import * as API from 'src/api/api.js';
//import workerSrc from 'https://mozilla.github.io/pdf.js/build/pdf.mjs'
//import { GlobalWorkerOptions } from 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.7.76/build/pdf.min.mjs'

import { Config } from 'src/config.js';
import * as pdfjsLib from 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.7.76/build/pdf.min.mjs';
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.7.76/build/pdf.worker.min.mjs'
// Use require because import doesn't work for some obscure reason. Also use `webpackChunkName` so it will not bundle this huge lib in your main code

// Now you assign the worker file path to the `pdfjsLib` (yes, it's that cumbersome)

// Add PDF.js script and worker
//var { pdfjsLib } = globalThis;
//pdfjsLib.GlobalWorkerOptions.workerSrc = '//mozilla.github.io/pdf.js/build/pdf.worker.mjs';//'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

const store = useStore();

const container = ref(null);
const pdfCanvas = ref(null);
let pdfDoc = null;
const scale = ref(1); // Initial value will be computed
const totalPages = ref(0); // Add this to track total pages

// Add a reactive variable to track page renders
const pagesRendered = ref(0);

// Add function to compute scale
async function computeScale(pageNumber = 1) {
  if (!pdfDoc || !container.value) return;
  
  // Get the specified page to calculate scale
  const page = await pdfDoc.getPage(pageNumber);
  const viewport = page.getViewport({ scale: 1.0 });
  
  // Calculate scale based on container width
  // Subtract 20px to account for padding/borders
  scale.value = (container.value.clientWidth - 20) / viewport.width;
}

// Load and render PDF
async function loadPDF() {
  try {
    console.log("before request");
    let originalUrl = null;
    if (store.pdfViewerData.documentPath) {
      originalUrl = store.pdfViewerData.documentPath;
    }
    else {
      const result = await store.getDocumentInfo(store.pdfViewerData.documentId);
      originalUrl = result.category + '/' + result.filename;
    }
    // if originalUrl starts with "Document: ", remove the prefix:
    if (originalUrl.startsWith("Document: ")) {
      originalUrl = originalUrl.substring("Document: ".length)
    }
    let url = originalUrl;
    console.log("after get url:", url);
    
    pdfDoc = await pdfjsLib.getDocument({
      url: url,
      withCredentials: false  // Set this to false when using the proxy
    }).promise;
    
    totalPages.value = pdfDoc.numPages;
    
    await renderAllPages(); // This now handles computing scale for the target page
  } catch (error) {
    console.error('Error loading PDF:', error);
  }
}

// Add new renderAllPages function
async function renderAllPages() {
  if (!pdfDoc || !container.value) return;

  // Remove any existing canvas elements
  const canvasElements = container.value.querySelectorAll('.pdf-canvas');
  canvasElements.forEach(el => el.remove());

  // If we're jumping to a specific page, compute scale based on that page
  if (store.pdfViewerData.pageNumber) {
    await computeScale(store.pdfViewerData.pageNumber);
  }

  // Render each page
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    try {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale: scale.value });

      // Create a new canvas for this page
      const canvas = document.createElement('canvas');
      canvas.id = `page-${pageNum}`;
      canvas.className = 'pdf-canvas';
      container.value.appendChild(canvas);

      const context = canvas.getContext('2d');
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      await page.render({
        canvasContext: context,
        viewport: viewport
      }).promise;
    } catch (error) {
      console.error(`Error rendering page ${pageNum}:`, error);
    }
  }
  
  // Increment the reactive count to trigger re-computation of the highlight style
  pagesRendered.value++;

  // Scroll to the target page after rendering
  if (store.pdfViewerData.pageNumber && container.value) {
    const pageElement = document.getElementById(`page-${store.pdfViewerData.pageNumber}`);
    if (pageElement) {
      // Get the offset of the target page relative to the container
      // const containerRect = container.value.getBoundingClientRect();
      // const pageRect = pageElement.getBoundingClientRect();
      // const relativeOffset = pageRect.top - containerRect.top;
      
      // Scroll the container
      // container.value.scrollTop = relativeOffset;
      pageElement.scrollIntoView({ behavior: 'smooth' });
    }
  }
}

// Watch for changes in URL or page number
watch([() => store.pdfViewerData, () => store.pdfViewerData.pageNumber], () => {
    loadPDF();
});

const highlightStyle = computed(() => {
  if (store.pdfViewerData.documentPath) {
    return {};
  }
  // Add a dummy dependency so that this computed property
  // re-runs when pagesRendered.value changes.
  const dummy = pagesRendered.value;
  
  // Check for required values explicitly (allowing pageNumber 0)
  if (!container.value || !store.pdfViewerData.highlight || store.pdfViewerData.pageNumber == null) {
    return {};
  }
  
  // Find the canvas for the specific page.
  const pageElement = document.getElementById(`page-${store.pdfViewerData.pageNumber}`);
  if (!pageElement) {
    return {};
  }
  
  // Extract the offset information from the canvas
  const { offsetLeft, offsetTop, offsetWidth, offsetHeight } = pageElement;
  // Compute pixel values relative to the page canvas based on percentage values in store.pdfViewerData.highlight
  const left = offsetLeft + (store.pdfViewerData.highlight.x) * offsetWidth;
  const top = offsetTop + (store.pdfViewerData.highlight.y) * offsetHeight;
  const width = (store.pdfViewerData.highlight.width) * offsetWidth;
  const height = (store.pdfViewerData.highlight.height) * offsetHeight;
  
  return {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
  };
});

onMounted(() => {
  if (!store.pdfViewerData.pageNumber) {
    console.warn("PDF Source is required");
    return;
  }
  loadPDF();
});

async function hidePdfViewer() {
  await nextTick();
  store.pdfViewerData.show = false;
}
</script>

<style scoped>
.pdf-viewer {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.pdf-header {
  position: sticky;
  top: 0;
  z-index: 10;
}
.pdf-container {
  position: relative;
  /* z-index: 1; */
  /* width: 100%;
  height: 100%;  */
  overflow: auto;
  background-color: #fff;
  border: 1px solid #ccc;
}

.pdf-canvas {
  display: block;
  z-index: 1;
  width: 100%;
  height: auto;
  margin-bottom: 10px; /* Add spacing between pages */
}

.highlight {
  position: absolute;
  background-color: rgba(147, 205, 238, 0.5);
  pointer-events: none;
  z-index: 999999;
}
</style>
