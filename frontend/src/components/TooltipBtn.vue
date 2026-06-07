<template>
    <q-btn @click="handleClick" no-caps dense size="sm" :class="btnClass" v-bind="$attrs">
        <tooltip v-if="tooltip">{{ tooltip }}</tooltip>
    </q-btn>
</template>

<script setup>
import Tooltip from 'src/components/Tooltip.vue'

const props = defineProps({
    tooltip: {
        type: String,
        default: null
    },
    btnClass: {
        type: String,
        default: ''
    }
});

const emits = defineEmits(['click']);

// Handle the button click and emit the event
const handleClick = () => {
    // Emit a 'click' event
    emits('click');
};
</script>
