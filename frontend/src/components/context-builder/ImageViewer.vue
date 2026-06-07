<template>
  <div class="p-d-flex p-justify-center">
    <div ref="imageContainer" v-if="hasImage" :style="{ width: '75%', height: popupHeight + 'px' }">
        <img :src="excerpt[2].image" style="width: 100%; height: 100%; object-fit:contain" @load="calculatePopupHeight" />
    </div> 
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
    doc: Object,
    excerpt: Object
});

const popupHeight = ref(600); // Default height
const imageContainer = ref(null);

function calculatePopupHeight(event) {
  const img = event.target;
  const naturalWidth = img.naturalWidth;
  const naturalHeight = img.naturalHeight;
  // calculate width of imageContainer:
  const containerWidth = imageContainer.value.clientWidth;
  
  if (naturalWidth && naturalHeight) {
    const aspectRatio = naturalHeight / naturalWidth;
    popupHeight.value = Math.min(containerWidth, Math.round(containerWidth * aspectRatio));
  }
}

const hasImage = computed(() => {
  for (let i = props.excerpt[0]; i <= props.excerpt[1]; i++) {
    if (props.doc.chunks[i].region.image_url) {
      props.excerpt[2].image = props.doc.chunks[i].region.image_url
      return true
    }
  }
  return false;
})
</script>

