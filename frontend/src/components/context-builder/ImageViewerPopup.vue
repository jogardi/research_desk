<template>
    <div v-if="hasImage">
        <q-btn flat dense round icon="image" color="info" style="cursor: pointer;">
        <q-popup-proxy :style="{ width: '575px', height: popupHeight + 'px' }"
            anchor="top middle" self="bottom right" :offset="[150, 0]">
            <div>
                <img :src="excerpt[2].image" style="width: 100%; height: 100%; object-fit: contain;" @load="calculatePopupHeight" />
            </div>
        </q-popup-proxy>
        </q-btn>
    </div> 
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
    doc: Object,
    excerpt: Object
});

const popupHeight = ref(600); // Default height

function calculatePopupHeight(event) {
  const img = event.target;
  const naturalWidth = img.naturalWidth;
  const naturalHeight = img.naturalHeight;
  
  if (naturalWidth && naturalHeight) {
    const aspectRatio = naturalHeight / naturalWidth;
    popupHeight.value = Math.min(575, Math.round(575 * aspectRatio));
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

