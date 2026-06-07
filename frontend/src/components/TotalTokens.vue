<template>
    <q-card id="token-usage" v-if="sessionStore.session && sessionStore.session.model" flat class="q-pa-sm q-mb-sm">
        <div class="subtitle flex justify-between">
            <span class="text-subtitle1">Model <span>{{ usageType }}</span> Usage</span>
            <q-btn @click="toggle()" :label="toggleLabel" no-caps flat Xoutline color="primary" size="sm" style="margin-top: -5px;" />
        </div>
        <div class="q-mt-sm">Model: {{ sessionStore.session.model.label }}</div>
        <div Xstyle="margin-top: -5px;" class="Xlegend flex justify-between q-mt-sm"
            :class="`${sessionStore.session.model.contextWindow - store.totalTokens <= 0? 'text-negative' : ''}`">
            <span>Used: {{ totalTokens }}</span>
            <span>
                <span class="q-mr-sm">Remainig: {{ remainingTokens }}</span> 
                <span>{{ remainingPercent }}</span>
            </span>
        </div>
        <div >Model Max: {{ calcUsage(sessionStore.session.model.contextWindow) }}</div>  
    </q-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'src/stores/main-store';
import { useSessionStore as useSessionStore } from 'src/stores/session-store';

const store = useStore()
const sessionStore = useSessionStore()

const toggleLabel = ref('Words')

function formatInt(value) {
    return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

function formatPecent(value) {
    return '(' +(value *100).toFixed(1) + '%)'
}

function toggle() {
    if (toggleLabel.value == 'Words') {
        toggleLabel.value = 'Tokens'
    } else {
        toggleLabel.value = 'Words'
    }
}

const totalTokens = computed(() => calcUsage(store.totalTokens))
const remainingTokens = computed(() => calcUsage(sessionStore.session.model.contextWindow - store.totalTokens))
const remainingPercent = computed(() => formatPecent((sessionStore.session.model.contextWindow - store.totalTokens)/sessionStore.session.model.contextWindow))

function calcUsage(value) {
    if (toggleLabel.value == 'Words') {
        return formatInt(value);
    } 
    else {
        const TOKENS_PER_WORD_RATIO = 1.5 // 1.5 tokens per word - this is an average value across different language models (1.2 - 1.5)
        return formatInt(Math.round(value / TOKENS_PER_WORD_RATIO));
    }
}


const usageType = computed(() => {
    if (toggleLabel.value == 'Words') {
        return 'Token'
    } else {
        return 'Word'
    }
})
</script>