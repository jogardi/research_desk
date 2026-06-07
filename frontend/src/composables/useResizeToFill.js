import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

/*
*  Resize the chunk list container to fill the remaining height of the page
*/
export default function useResizeToFill(bottomOffset = 15) {
  const listContainer = ref(null);

  const remainingHeight = computed(() => {
    if (!listContainer.value) return 0;
    const windowHeight = window.innerHeight;
    // const elementTop = listContainer.value.getBoundingClientRect().top;
    const elementBottom = listContainer.value.getBoundingClientRect().bottom;
    return windowHeight - elementBottom - bottomOffset;
  });

  function updateHeight() {
    if (listContainer.value) {
      listContainer.value.style.height = `${remainingHeight.value}px`;
    }
  }

  onMounted(() => {
    window.addEventListener('resize', updateHeight);
    updateHeight();
  });

  onBeforeUnmount(() => {
    window.removeEventListener('resize', updateHeight);
  });

function scrollTo(direction) {
  if (listContainer.value) {
    let pos = 0; // default to top
    if (direction === 'bottom') {
      pos = listContainer.value.scrollHeight;
    }
    listContainer.value.scrollTop = pos;
  }
}

  return { listContainer, remainingHeight, scrollTo };
}