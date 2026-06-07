<template>
    <div ref="editorEl" style="width: 100%;"></div>
  </template>
  
  <script setup>
    import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
    import Editor from '@toast-ui/editor';
    import colorSyntax from '@toast-ui/editor-plugin-color-syntax';
    import { useQuasar } from 'quasar'
    
    import { useSessionStore } from 'src/stores/session-store';
    
    const $q = useQuasar()
    const sessionStore = useSessionStore();

    // const props = defineProps({
    //     modelValue: String
    // });
    // const emit = defineEmits(['update:modelValue']);

    const editorEl = ref(null);
    let editorInstance = null;

    const colorSyntaxOptions = {
        preset: ['#26A69A', '#1676C8', '#9C27B0', '#31CCEC', '#F2C037', '#C10015', '#f6eb76', '#ffffff']
    };

  
    onMounted(() => {
        editorInstance = new Editor({
        el: editorEl.value,
        height: window.innerHeight - 140 + 'px',
        initialEditType: 'wysiwyg',
        previewStyle: "vertical",
        theme: $q.dark.isActive ? 'dark' : 'light',
        initialValue: sessionStore.session.notes,
        plugins: [[colorSyntax, colorSyntaxOptions]]
        });

        editorInstance.on('change', () => {
            sessionStore.session.notes = editorInstance.getMarkdown();
            // emit('update:modelValue', content);
        });
    });
    
    onBeforeUnmount(() => {
        // editorInstance.off('change');
        editorInstance.destroy();
    });

    // watch(() => props.modelValue, (newValue) => {
    //     if (editorInstance && editorInstance.getMarkdown() !== newValue) {
    //         editorInstance.setMarkdown(newValue);
    //     }
    // }, 
    // { immediate: true });
  </script>