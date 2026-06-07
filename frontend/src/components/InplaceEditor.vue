<template>
    <div class="editor-container">
      <div class="subtitle p-d-flex p-justify-center text-info"><span>Edit Excerpt</span></div>
      <!-- Editable text area -->
      <q-input type="textarea" autogrow  filled class="editor-textarea" v-model="tempText" Xrows="5" 
        @keydown.esc="cancel"Xclass="q-input q-mb-md">
        <template v-slot:append>
            <div class="p-d-flex p-justify-content-end Xq-gutter-xs Xp-mb-0 Xp-mr-1">        
                <q-btn Xlabel="Cancel" round flat color="negative" @click="cancel" size="sm" icon="cancel">
                    <tooltip>Cancel</tooltip>
                </q-btn>
                <q-btn Xlabel="Save" round  flat color="positive" @click="save" size="sm" icon="check">
                    <tooltip>Save</tooltip>
                </q-btn>
            </div>
        </template>
      </q-input>
      <div style="height: 0px; padding: 0px; overflow: hidden;">{{tempText}}</div>
    </div>
  </template>
  
  <script setup>
  import { ref, watch, onMounted, onUnmounted } from 'vue';
  import Tooltip from 'src/components/Tooltip.vue'
  
  // Props for v-model binding
  const props = defineProps({
    modelValue: { type: String, required: true }, // Bound value from parent (v-model)
  });
  
  // Emits
  const emit = defineEmits(['update:modelValue', 'cancel']); // Emits for v-model and cancel
  
  // Local state for the editor
  const tempText = ref(props.modelValue); // Initialize with the bound value
  
  // Watch for changes to modelValue and sync tempText
  watch(
    () => props.modelValue,
    (newValue) => {
      tempText.value = newValue;
    }
  );
  
  // Save method: emit updated text to v-model
  function save() {
    emit('update:modelValue', tempText.value); // Update the parent's value
  }
  
  // Cancel method: reset tempText to the bound value
  function cancel() {
    tempText.value = props.modelValue; // Restore to original value
    emit('cancel'); // Notify parent of the cancel action
  }

  </script>
  
  <style scoped>
  .editor-container {
    background-color: transparent;
    width: 100%;
  }
  
.editor-textarea {
  width: 100%;
  /* background-color: transparent; */
  color: var(--body-text-color); /* Use Quasar's grey-9 color */
  border: none; /* Remove the border */
}

textarea {
  font-size: 1rem;
  line-height: 25px !important;
}
</style>


  