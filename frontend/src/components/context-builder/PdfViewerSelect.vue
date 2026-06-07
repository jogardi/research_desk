<template>
  <div class="pdf-viewer">
    <!-- Make the header fixed -->
    <q-toolbar class="pdf-header p-d-flex p-justify-content-between p-align-items-center text-positive  bg-body-color">
      <q-toolbar-title>PDF Viewer</q-toolbar-title>
      <!-- <div class="title Xtext-h6 p-px-0">PDF Viewer</div> -->
      <q-btn @click="hidePdfViewer()" dense flat size="sm" color="primary" icon="close" />
    </q-toolbar>
    
    <!-- Add padding-top to the container to account for the fixed header -->
    <div ref="container" class="pdf-container">
      <!-- Text layers for all pages -->
      <div v-for="pageNum in totalPages" :key="pageNum" :id="`textLayer-${pageNum}`" class="text-layer"></div>
      <!-- Highlight overlay -->
      <div v-if="highlightStyle" class="highlight" :style="highlightStyle"></div>>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from "vue";
import { useStore } from 'src/stores/main-store';
import * as pdfjsLib from 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.7.76/build/pdf.min.mjs';

// Set the worker source for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@4.7.76/build/pdf.worker.min.mjs';

// Store and reactive refs
const store = useStore();
const container = ref(null);
const totalPages = ref(0);
const isRendered = ref(false); // Track rendering completion
let pdfDoc = null;
const scale = ref(1);

const isLoading = ref(false);

// Load the PDF and render all pages
async function loadPDF() {
  try {
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
      originalUrl = originalUrl.substring("Document: ".length);
    }
    let url = originalUrl;

    // Load the PDF document
    pdfDoc = await pdfjsLib.getDocument({ url }).promise;
    totalPages.value = pdfDoc.numPages;
    console.log(`PDF loaded successfully with ${totalPages.value} pages`);

    // Wait for DOM update
    await nextTick();
    await renderAllPages();
    isRendered.value = true; // Mark rendering complete
  } catch (error) {
    console.error("Error loading PDF:", error);
  }
}

// Render all pages
async function renderAllPages() {
  if (!pdfDoc || !container.value) {
    console.warn("Cannot render: PDF or container not available");
    return;
  }

  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    const textLayer = document.getElementById(`textLayer-${pageNum}`);
    if (!textLayer) {
      console.warn(`Text layer for page ${pageNum} not found`);
      continue;
    }

    try {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.0 });

      // Adjust scale to fit container width
      scale.value = (container.value.clientWidth - 20) / viewport.width;
      const scaledViewport = page.getViewport({ scale: scale.value });

      // Clear previous text layer content
      textLayer.innerHTML = "";

      // Manual text rendering
      const textContent = await page.getTextContent();
      console.log(`Page ${pageNum} has ${textContent.items.length} text items`);
      textContent.items.forEach((item) => {
        const div = document.createElement('div');
        div.textContent = item.str;
        div.style.position = 'absolute';
        div.style.left = `${item.transform[4] * scale.value}px`;
        div.style.top = `${(viewport.height - item.transform[5] - item.height) * scale.value}px`;
        div.style.fontSize = `${item.height * scale.value}px`;
        textLayer.appendChild(div);
      });

      // Set text layer dimensions
      textLayer.style.width = `${scaledViewport.width}px`;
      textLayer.style.height = `${scaledViewport.height}px`;
      console.log(`Page ${pageNum} rendered with width: ${scaledViewport.width}px, height: ${scaledViewport.height}px`);

      // Scroll to the specified page
      if (pageNum === (store.pdfViewerData.pageNumber || 1)) {
        textLayer.scrollIntoView({ behavior: 'smooth' });
      }
    } catch (error) {
      console.error(`Error rendering page ${pageNum}:`, error);
    }
  }
}

// Highlight style based on percentage values
const highlightStyle = computed(() => {
  if (!isRendered.value || !store.pdfViewerData.highlight || !store.pdfViewerData.pageNumber) {
    console.log("Highlight skipped: Not rendered or no highlight data:", {
      isRendered: isRendered.value,
      highlight: store.pdfViewerData.highlight,
      pageNumber: store.pdfViewerData.pageNumber
    });
    return null;
  }

  const pageNum = store.pdfViewerData.pageNumber || 1;
  const textLayer = document.getElementById(`textLayer-${pageNum}`);
  if (!textLayer) {
    console.warn(`Highlight: Text layer for page ${pageNum} not found`);
    return null;
  }

  const { x, y, width, height } = store.pdfViewerData.highlight;
  const layerWidth = textLayer.clientWidth;
  const layerHeight = textLayer.clientHeight;
  const layerTop = textLayer.offsetTop;

  const style = {
    left: `${x * layerWidth}px`,
    top: `${layerTop + y * layerHeight}px`,
    width: `${width * layerWidth}px`,
    height: `${height * layerHeight}px`,
    backgroundColor: 'rgba(147, 205, 238, 0.5)',
    border: '1px solid blue'
  };
  console.log(`Highlight style for page ${pageNum}:`, style);
  return style;
});

// Manual trigger for updates
const refreshPDF = async () => {
  await loadPDF();
};

// Initial load
onMounted(async () => {
  await loadPDF();
});

onUnmounted(async () => {
  await nextTick();
  store.pdfViewerData.show = false;
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
  /* flex: 1; */
  overflow-y: auto;
  background-color: #fff;
  border: 1px solid #ccc;
}

.text-layer {
  position: relative;
  color: #000;
  user-select: text;
  -webkit-user-select: text;
  -moz-user-select: text;
  -ms-user-select: text;
  margin-bottom: 10px;
}

.text-layer > div {
  position: absolute;
  white-space: pre;
  cursor: text;
}

.highlight {
  position: absolute;
  background-color: rgba(147, 205, 238, 0.5);
  pointer-events: none;
  z-index: 10;
}
</style>
