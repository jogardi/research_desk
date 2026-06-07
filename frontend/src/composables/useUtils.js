import { ref, nextTick } from 'vue';
import { useStore } from 'src/stores/main-store';
import { useSessionStore } from 'src/stores/session-store';
import { useCategoryStore } from 'src/stores/category-store';
import { useModelStore } from 'src/stores/model-store';
import { Dialog } from 'quasar'
import { getDocumentsText, getExcerptText } from 'src/utils/docUtils.js';
import { generateExcerptHash } from 'src/utils/excerptUtils.js';

export default function useUtils() {
  const store = useStore();
  const sessionStore = useSessionStore();
  const categoryStore = useCategoryStore();
  const modelStore = useModelStore();
  
  // Store citation metadata
  let citationMetadata = ref({});
  
  // Construct a system message from the selected system prompt
  async function constructSystemMessage() {
    // set llm role instructions
    let llmRoleInstructions = ''
    const selectedLlmRole = store.getSelectedLlmRole();

    if (selectedLlmRole && sessionStore.session.model.useRoles) {
      console.log('*** Using Roles!!!!')
      llmRoleInstructions = selectedLlmRole.role;
      // if (llmRoleInstructions[llmRoleInstructions.length - 1] != '.') {
      //   llmRoleInstructions += '.';
      // }
      llmRoleInstructions += '\n\n';
  }
  else {
    console.log('*** NOT Using Roles!!!!')
  }

    // Create hashed excerpts with metadata
    const { contextText, metadata } = await createHashedExcerpts();
    citationMetadata.value = metadata;
    
    let citationsInstructions = 'Each excerpt is identified by a 4-character hash for citation purposes.\n\n';
    citationsInstructions += '- Include citations where appropriate.\n';
    citationsInstructions += '- Citations should be formatted as hash codes in square brackets, e.g., [a1b2], [c3d4], etc., where the hash code corresponds to the excerpt\'s unique identifier.\n';
    citationsInstructions += '- Example: If you use information from an excerpt with hash a1b2, write: "According to the study, the results showed... [a1b2]."\n';
    citationsInstructions += '- If you use information from multiple excerpts, you can cite them together: "Multiple sources confirm this finding [a1b2][c3d4]."\n';
    citationsInstructions += '- You can cite both the excerpts provided below AND any excerpts returned by the searchSemanticByDoc tool.\n\n';
    
    const excerptsInstructions = 'Here are excerpts selected by the user that they are interested in asking about.\n\nEXCERPTS:\n\n' + contextText;
  
    const includeInstructions = "You can use both your own knowledge/opinions and these excerpts selected by the user to answer the user's question.\n\n"
    const excludeInstructions = "Use only the text in the provided excerpts as context when answering user queries. Do not use your general knowledge base.\n\n";
    // set include or exclude instructions
    let includeExcludeInstructions = includeInstructions;
    if (sessionStore.session.chatsExcludeInclue[sessionStore.session.model.value] == 'Exclude') {
      includeExcludeInstructions = excludeInstructions;
    }
      
    const systemMessageContent = llmRoleInstructions + 
                                includeExcludeInstructions + "\n\n" + 
                                citationsInstructions + "\n\n" + 
                                excerptsInstructions;
    
    console.log('systemMessage:\n' + systemMessageContent);
    return { role: 'system', content: systemMessageContent }
  }

  // Create hashed excerpts from context documents
  async function createHashedExcerpts() {
    const contextDocs = sessionStore.session.contextDocs;
    let contextText = '';
    const metadata = {};

    for (const doc of contextDocs) {
      for (const excerpt of doc.excerpts) {
        // Generate hash for this excerpt
        const chunkIds = [];
        for (let i = excerpt[0]; i <= excerpt[1]; i++) {
          chunkIds.push(doc.chunks[i].id);
        }
        
        const hash = await generateExcerptHash(doc.documentID, chunkIds);
        const excerptText = getExcerptText(excerpt, doc.chunks);
        
        contextText += `[Excerpt ${hash}]\n`;
        contextText += `Source: ${doc.documentName}\n`;
        contextText += excerptText + '\n\n';

        // Store metadata for this excerpt
        metadata[hash] = {
          hash: hash,
          documentID: doc.documentID,
          documentName: doc.documentName,
          excerpt: excerpt,
          chunkIds: chunkIds,
          // Get page number from first chunk in excerpt
          pageNumber: doc.chunks[excerpt[0]].region ? doc.chunks[excerpt[0]].region.page_number : null
        };
      }
    }

    return { contextText, metadata };
  }

  // Get citation metadata for use in Chat.vue
  async function getCitationMetadata() {
    if (!citationMetadata.value || Object.keys(citationMetadata.value).length === 0) {
      const { contextText, metadata } = await createHashedExcerpts();
      citationMetadata.value = metadata;
    }
    return citationMetadata.value;
  }

  // Update the total tokens in the session (includes only messages for selected model)
  async function updateTotalTokens() {
    const totalTokensWasPositive = sessionStore.session.model.contextWindow - store.totalTokens > 0;

    const systemMessage = await constructSystemMessage();
    store.totalTokens = _estimatedTokens(systemMessage.content);

    const messages = sessionStore.session.chats[sessionStore.session.model.value];
    messages.forEach(message => {
      store.totalTokens += _estimatedTokens(message.content);
    });

    const remainingTokens = sessionStore.session.model.contextWindow - store.totalTokens;
    if (remainingTokens <= 0 && totalTokensWasPositive) {
      Dialog.create({
        title: 'Conext Too Large',
        message: "The total number of tokens exceeds the currently selected AI model's window context size. Please remove some chat messages or reduce context size.",
        persistent: true
      });
    }
    return store.totalTokens;
  }

  function  checkTokensExceed(systemMessage) {
    const totalTokensWasPositive = sessionStore.session.model.contextWindow - store.totalTokens > 0;
    let totalTokens = store.totalTokens;
    totalTokens += _estimatedTokens(systemMessage.content);
    const messages = sessionStore.session.chats[sessionStore.session.model.value];
    messages.forEach(message => {
      totalTokens += _estimatedTokens(message.content);
    });
    const remainingTokens = sessionStore.session.model.contextWindow - totalTokens;
    if (remainingTokens <= 0 && totalTokensWasPositive) {
      Dialog.create({
        title: 'Conext Too Large',
        message: "The total number of tokens would exceed the currently selected AI model's window context size. Please remove some chat messages or reduce context size.",
        persistent: true
      });

      return true
    }
    return false;
  }

  // Estimate the number of tokens in a text
  function _estimatedTokens(text) {
    // Define the average ratio of tokens to words
    const TOKENS_PER_WORD_RATIO = 1.5 // 1.5 tokens per word - this is an average value across different language models (1.2 - 1.5)
    const numWords = text.split(' ').length;
    return Math.round(numWords * TOKENS_PER_WORD_RATIO);
  }

  // Update the selected categories from ticked nodes
  // function updateSelectedCategoryPaths() {
  //   nextTick(() => {
  //       categoryStore.selectedCategoryPaths = []; // Reset current labels

  //       sessionStore.session.categories.forEach(id => {
  //       const path = _findPath(categoryStore.categoryTreeData, id); // Find the path for each ticked node
  //       if (path) {
  //           // const pathStr = path.slice(1).join('/'); // Remove the root node from the path and join the path parts
  //           const pathStr = path.join('/'); // join the path parts
  //           categoryStore.selectedCategoryPaths.push(pathStr); // Add the path to the labels
  //       }
  //       });
  //       // sort labels:
  //       categoryStore.selectedCategoryPaths.sort((a, b) => a.localeCompare(b));
  //   });
  // }

  // Find the path to a node in a tree
  // function _findPath(nodes, id, path = []) {
  //   for (const node of nodes) {
  //     // Current path for this iteration
  //     const currentPath = [...path, node.label]; // Add the current node to the path

  //     if (node.id === id) {
  //       // Return the path when the node is found
  //       return currentPath;
  //     } 
  //     else if (node.children && node.children.length > 0) {
  //       // Continue searching in children
  //       const resultPath = _findPath(node.children, id, currentPath);
  //       if (resultPath) {
  //         return resultPath; // Return the found path
  //       }
  //     }
  //   }
  //   return null; // Return null if the node is not found
  // }

  return {
    constructSystemMessage,
    updateTotalTokens,
    checkTokensExceed,
    getCitationMetadata
    // updateSelectedCategoryPaths
  }
}
