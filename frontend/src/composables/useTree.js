import { ref } from 'vue'
import fuzzysort from 'fuzzysort'
import { useCategoryStore } from 'src/stores/category-store';

export default function useTree() {
// const ROOT = 'All Categories'
const options = ref([])

const categoryStore = useCategoryStore();

// generate the path of a node in the tree
function generatePath(node) {
    let path = []
    let currentNode = node
  
    while (currentNode) {
      path.unshift(currentNode.label)   
      currentNode = currentNode.parent 
    }
  
    path = path.join('/')
    // path = path.replace('/'+ROOT+'/', '') // remove the leading "/All Categories/" from the path
    path = path.substring(1) // remove the leading '/' from the path
    return path;
  }

  // perform fuzzy search on the category list for given query
  const remoteMethod = (query) => {
    if (!query || query === '') {
      options.value = [];
      return;
    }
  
    // Fuzzy string matching
    const fuzzyResults = fuzzysort.go(query, categoryStore.categoryListData, {
      key: 'label',
      threshold: 0.3
    });
  
    const results = fuzzyResults.map((result) => result.obj);
    const uniqueResults = [...new Set(results)];
  
    // Set options to matched results so user can select from them:
    options.value = uniqueResults;
  };

  // generate the complete list of options for the select component
  function generateOptionsList(treeRef) {
    if (categoryStore.categoryListData.length > 0) { // if options list already loaded, done!
        return;
    }
    categoryStore.categoryListData = [] 
    categoryStore.categoryIDs.forEach((id) => {
      const node = treeRef.getNode(id)
      if (node) {
        const path = generatePath(node)
        categoryStore.categoryListData.push({ id: id,  label: path})
      }
    })
  }


return { options, generatePath, remoteMethod, generateOptionsList } 

}