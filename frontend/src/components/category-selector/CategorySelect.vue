<template>
    <el-select
        v-model="categoryStore.selectedCategories"
        value-key="id"
        multiple
        filterable
        remote
        no-data-text="No categories match your search term"
        reserve-keyword
        placeholder=""
        :remote-method="remoteMethod"
        @change="onChange"
        Xstyle="width: 800px"
        size="large"
        type="primary"
        >
        <el-option
            v-for="item in options"
            :key="item.value"
            :label="item.label"
            :value="item"
        />
    </el-select>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSessionStore } from "src/stores/session-store";
import { useCategoryStore } from "src/stores/category-store";
import useTree from "src/composables/useTree.js";

const { options, remoteMethod } = useTree()
const sessionStore = useSessionStore();
const categoryStore = useCategoryStore();

onMounted(() => {
})

function onChange(value) {
    sessionStore.session.categories = categoryStore.selectedCategories.map((category) => category.id)  
}
</script>