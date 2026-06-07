<template>
    <div v-if="chunk.documentID != -1">
        <q-btn flat icon="source" label="Source" color="primary" size="md" no-caps>
            <q-popup-proxy @before-show="getSoureDocInfo" class="q-pa-md" dark>
                <div>
                    <div v-if="sourceDocInfo != null">
                        <span class="text-bold">Category:</span> {{ sourceDocInfo.category }} <br />
                        <span class="text-bold">Document:</span> {{ sourceDocInfo.filename }} <br />
                    </div>
                    <span v-else class="text-warning">
                    <q-icon name="error"></q-icon> <span class="q-ml-xs">Source document flagged!</span>
                    </span>
                </div>
            </q-popup-proxy> 
        </q-btn>
    </div>
</template>

<script setup>
    import { ref } from 'vue'
    import { useStore } from 'src/stores/main-store';

    const store = useStore()

    const sourceDocInfo = ref(null)

    const props = defineProps({
        chunk: {
            type: Object,
            required: true
        }
    })

    async function getSoureDocInfo() {
        if (sourceDocInfo.value != null && sourceDocInfo.value.id == props.chunk.documentID) { // already loaded
        return
        }
        sourceDocInfo.value = await store.getDocumentInfo(props.chunk.documentID) // get document info from the server
        if (sourceDocInfo.value != null) {
            sourceDocInfo.value.id = props.chunk.documentID
        }
    }
</script>