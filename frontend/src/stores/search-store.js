import { defineStore } from "pinia";
import { ref } from "vue";
import * as API from 'src/api/api.js';
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import { useCategoryStore } from 'src/stores/category-store';

export const useSearchStore = defineStore('search', () => {
    // STORES:
    const store = useStore()
    const sessionStore = useSessionStore()
    const categoryStore = useCategoryStore();

    // STATE:
    const semanticDocs = ref([]) // chunks returned from the semantic search API call
    const textDocs = ref([]) // chunks returned from the semantic search API call
    // const semanticChunks = ref([]) // chunks returned from the semantic search API call
    const textChunks = ref([]) // chunks returned from the text search API call
    const semanticSearchQuery = ref('') // the query used for the semantic search
    const textSearchQuery = ref('') // the query used for the text search 

    // ACTIONS:
    async function semanticSearch(query) {
      semanticDocs.value = []
      const selectedCategoriesPaths = categoryStore.selectedCategories.map((category) => category.label)
      const categoriesPaths = _removeGeneral(selectedCategoriesPaths)
      
      const result = await API.semanticSearchByDoc(query, categoriesPaths, sessionStore.session.topK);
      
      if (result.isError) {
        return false;
      }
      
      semanticDocs.value = result.data;

      // Normalize the scores of the chunks
      // semanticDocs.value.forEach(doc => {
      //   let maxScore = 0;
      //   doc.chunks.forEach(chunk => {
      //     if (chunk.score != 2 && chunk.score > maxScore) {
      //       maxScore = chunk.score;
      //     }
      //   });
      //   // Normalize the scores of the chunks
      //   doc.chunks.forEach(chunk => {
      //     if (chunk.score != 2) {
      //       chunk.score = chunk.score / maxScore;
      //     }
      //   });
      // });
      console.log("got semantic docs")

      semanticDocs.value.forEach(doc => {
        doc.checked = false;
        doc.excerpts.forEach(excerpt => {
          doc.chunks[excerpt[0]].text = doc.chunks[excerpt[0]].text.replace(/^<br\/?>/, '');
          let scoreTotal = 0;
          let score2Count = 0;
          for (let i = excerpt[0]; i <= excerpt[1]; i++) {
            if (doc.chunks[i].score != 2) {
              scoreTotal += doc.chunks[i].score;
              // highlight the chunk
              doc.chunks[i].text = '<span class="hilite-sentence">' + doc.chunks[i].text + '</span>';
            }
            else {
              console.log("score was equal to 2")
              score2Count++;
            }
            // Convert http:// to https:// before linkification
            doc.chunks[i].text = doc.chunks[i].text.replace(/http:\/\//g, 'https://');
            // Replace URLs with clickable links
            doc.chunks[i].text = linkifyUrls(doc.chunks[i].text);

            if (doc.docType == 'CSV') {
              doc.chunks[i].text = _generateTableFromCSV(doc.chunks[i].text, '\n');
            }
          }          
          const chunkCount = excerpt[1] - excerpt[0] + 1 - score2Count;
          if (chunkCount > 0) {
            excerpt.push({checked: false, score: scoreTotal / chunkCount}) // average score of the chunks in the excerpt
          }
          else { // if there is only one chunk in the excerpt
            let score = doc.chunks[excerpt[0]].score 
            if (score == 2) {
              score = 0.000001;
            }
            excerpt.push({checked: false, score: score})
          }
        });
      });
      return true;
    }

    async function textSearch(query) {
      textDocs.value = []
      const selectedCategoriesPaths = categoryStore.selectedCategories.map((category) => category.label)
      const categoriesPaths = _removeGeneral(selectedCategoriesPaths)
      
      const result = await API.textSearchByDoc(query, categoriesPaths);
      
      if (result.isError) {
        return false;
      }
      
      textDocs.value = result.data;
      // Add a 'checked' property to excerpts
      textDocs.value.forEach(doc => {
        doc.checked = false;
        doc.excerpts.forEach(excerpt => {
          for (let i = excerpt[0]; i <= excerpt[1]; i++) {
            // Convert http:// to https:// before linkification
            doc.chunks[i].text = doc.chunks[i].text.replace(/http:\/\//g, 'https://');
            // Replace URLs with clickable links before highlighting
            doc.chunks[i].text = linkifyUrls(doc.chunks[i].text);
            
            if (doc.docType == 'CSV') {
              doc.chunks[i].text = _generateTableFromCSV(doc.chunks[i].text, '<br>');
            }

            if (doc.chunks[i].score != 2) {
              // highlight the chunk
              doc.chunks[i].text = '<span class="hilite-sentence">' + doc.chunks[i].text + '</span>';
            }
          }
          excerpt.push({checked: false})
        });
      });
      return true;  
    }

    function _generateTableFromCSV(text, lineBreakChar) {
      // Simple CSV parser that handles quoted fields
      const parseCSV = (row) => {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (const char of row) {
          if (char === '"') {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            result.push(current.trim());
            current = '';
          } else {
            current += char;
          }
        }
        result.push(current.trim());
        return result;
      };

      let table = '<table>';
      let rows = text.split(lineBreakChar);

      // Header row
      if (rows.length > 0) {
        table += '<thead><tr>';
        let cells = parseCSV(rows[0]);
        for (let j = 0; j < cells.length; j++) {
          table += '<th>' + cells[j] + '</th>';
        }
        table += '</tr></thead>';
      }

      // Body rows
      if (rows.length > 1) {
        table += '<tbody>';
        for (let i = 1; i < rows.length; i++) {
          table += '<tr>';
          let cells = parseCSV(rows[i]);
          for (let j = 0; j < cells.length; j++) {
            table += '<td>' + cells[j] + '</td>';
          }
          table += '</tr>';
        }
        table += '</tbody>';
      }

      table += '</table>';
      return table;
    }


    async function getSuggestedCategories(query) {
      return await API.getSuggestedCategories(query);
    }

    function _removeGeneral(categoriesPaths) {
      categoriesPaths = JSON.parse(JSON.stringify(categoriesPaths)) // clone the array
      for (let i = 0; i < categoriesPaths.length; i++) {
        if (categoriesPaths[i].endsWith('/General')) {
          categoriesPaths[i] = categoriesPaths[i].replace('/General', '') // remove '/General' from the path
        }
      }
      return categoriesPaths;
    }

    // Helper function to linkify URLs in text using DOM parsing
    function linkifyUrls(htmlText) {
      const div = document.createElement('div');
      div.innerHTML = htmlText;
  
      if (findAndLinkUrl(div)) {
          // If a URL was found and linked, the DOM has changed.
          // We recursively call the function to process the new HTML.
          // This handles multiple URLs and avoids complex DOM state management.
          return linkifyUrls(div.innerHTML);
      }
  
      return div.innerHTML;
  }
  
  function findAndLinkUrl(container) {
      const urlRegex = /(https?:\/\/|www\.)/;
      const allowedElements = ['B', 'I', 'U', 'STRONG', 'EM', 'SUB', 'SUP'];
      
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
          acceptNode(node) {
              if (node.parentElement.closest('a')) {
                  return NodeFilter.FILTER_REJECT;
              }
              if (node.nodeValue.match(urlRegex)) {
                  return NodeFilter.FILTER_ACCEPT;
              }
              return NodeFilter.FILTER_SKIP;
          }
      });
  
      const startNode = walker.nextNode();
      if (!startNode) {
          return false; // No URLs found
      }
  
      const match = startNode.nodeValue.match(urlRegex);
      const urlNode = startNode.splitText(match.index);
  
      const nodesToWrap = [];
      let href = '';
      let scanNode = urlNode;
      let urlFinished = false;
  
      // Helper for depth-first traversal
      function getNextNode(node) {
          if (node.firstChild) return node.firstChild;
          while (node) {
              if (node.nextSibling) return node.nextSibling;
              node = node.parentNode;
              if (node === container) return null;
          }
          return null;
      }
  
      while (scanNode && !urlFinished) {
          if (scanNode.nodeType === Node.TEXT_NODE) {
              const stopMatch = scanNode.nodeValue.match(/[\s\t\n\r<>()]/);
              if (stopMatch) {
                  const urlPart = scanNode.nodeValue.substring(0, stopMatch.index);
                  const restPart = scanNode.nodeValue.substring(stopMatch.index);
                  href += urlPart;
                  if (urlPart) {
                      scanNode.nodeValue = urlPart;
                      nodesToWrap.push(scanNode);
                  } else {
                      if (scanNode.parentNode) scanNode.parentNode.removeChild(scanNode);
                  }
                  
                  if (restPart) {
                      const restNode = document.createTextNode(restPart);
                      if (scanNode.parentNode) {
                        scanNode.parentNode.insertBefore(restNode, scanNode.nextSibling);
                      } else {
                        // This can happen if the node was removed.
                        // The logic gets complex, but for this case, it should be fine.
                        // A more robust solution might need to track the parent differently.
                      }
                  }
                  urlFinished = true;
              } else {
                  href += scanNode.nodeValue;
                  nodesToWrap.push(scanNode);
              }
          } else if (scanNode.nodeType === Node.ELEMENT_NODE && allowedElements.includes(scanNode.tagName)) {
              href += scanNode.textContent;
              nodesToWrap.push(scanNode);
          } else {
              urlFinished = true;
              continue;
          }
  
          if (!urlFinished) {
              scanNode = getNextNode(scanNode);
          }
      }
  
      if (nodesToWrap.length > 0) {
          const range = document.createRange();
          range.setStartBefore(nodesToWrap[0]);
          range.setEndAfter(nodesToWrap[nodesToWrap.length - 1]);
          
          const a = document.createElement('a');
          a.target = '_blank';
          const finalHref = href.startsWith('www.') ? 'https://' + href : href;
          a.href = finalHref.replace(/<[^>]*>/g, '');
          
          try {
            range.surroundContents(a);
          } catch(e) {
            // It can fail if the range is not well-formed.
            // In that case, we can fallback to a simpler method.
            a.innerHTML = href;
            range.deleteContents();
            range.insertNode(a);
          }
          return true;
      }
  
      return false;
  }

    return {
      semanticDocs, textDocs, semanticSearchQuery, textSearchQuery,
        semanticSearch, textSearch, getSuggestedCategories, _removeGeneral
    };
    
});

