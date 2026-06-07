<template>
    <q-card class="notes-report p-p-0">
        <q-toolbar>
          <q-toolbar-title><q-icon name="comments" class="p-ml-3"></q-icon>Notes for Thought Flow: {{sessionStore.session.name}}</q-toolbar-title>
            <q-space />
            <!-- <q-btn icon="save" label="Save" color="primary" class="q-mr-lg" v-close-popup/> -->
            <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>
        <q-card-section class="row items-center p-p-0">
        <ToastEditor />
        </q-card-section>
    </q-card>
</template>

<script setup>
import { ref } from 'vue';
import { useQuasar } from 'quasar'
import ToastEditor from 'src/components/ToastEditor.vue';
import { useSessionStore } from 'src/stores/session-store';

const $q = useQuasar()
    
const sessionStore = useSessionStore()

</script>