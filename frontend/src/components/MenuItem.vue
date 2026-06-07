<template>
    <q-item @click="handleClick" clickable v-close-popup>
        <q-item-section side>
            <q-icon :color="color" :name="icon" size="xs" />
        </q-item-section>
        <q-item-section><slot></slot></q-item-section>
    </q-item>
</template>

<script setup>

const props = defineProps({
    icon: {
        type: String,
        required: true
    },
    color: {
        type: String,
        required: true
    }
});

const emits = defineEmits(['click']);

// Handle the button click and emit the event
const handleClick = () => {
    // Emit a 'click' event
    emits('click');
}
</script>
