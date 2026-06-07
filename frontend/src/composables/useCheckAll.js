import { computed, ref } from 'vue';
import { useSessionStore } from 'src/stores/session-store';
import { useSearchStore } from 'src/stores/search-store';

export default function useCheckAll(source) {
  const sessionStore = useSessionStore();
  const searchStore = useSearchStore();

  const checkedCount = ref(0);
  const excerptCount = ref(0);

  // initialized checkedCount and excerptCount
  updateCounts();

  function updateCounts() {
    const docs = getDocs();
    checkedCount.value = 0;
    excerptCount.value = 0;
    docs.forEach(doc => {
      doc.excerpts.forEach(excerpt => {
        if (excerpt[2].checked) {
          checkedCount.value++;
        }
        excerptCount.value++;
      });
    });
  }

  function getDocs() {
    if (source == 'semantic-search') {
      return searchStore.semanticDocs;
    }
    else if (source == 'text-search') {
      return searchStore.textDocs;
    }
    else if (source == 'context') {
       return sessionStore.session.contextDocs;
     }
     else if (source == 'stash') {
       return sessionStore.session.stashDocs;
     }

  }

  function onCheckboxClicked(value, evt) {
    // update checkedCount
    if (value) {
      checkedCount.value++;
    }
    else {
      checkedCount.value--;
    }
    // update excerptCount
    excerptCount.value = 0;
    const docs = getDocs();
    docs.forEach(doc => {
      excerptCount.value += doc.excerpts.length;
    });
  }

  function checkAll(value, excludeBelowMinSimilarityScore = false) {
    excludeBelowMinSimilarityScore = false; // remove this line
      const docs = getDocs();
      docs.forEach(doc => {
        doc.checked = value;
        doc.excerpts.forEach(excerpt => {
          if (excludeBelowMinSimilarityScore) {
            if (excerpt.score >= sessionStore.session.minSimilarityScore/10) {
              excerpt[2].checked = value
            }
          }
          else {
            excerpt[2].checked = value
          }
        });
      });

      checkedCount.value = value? excerptCount.value : 0;
    }


  return { checkedCount, excerptCount, onCheckboxClicked, checkAll, updateCounts };
}
