<template>
    <div class="relative">
        <UButton :label="label" color="primary" @click="triggerFileInput">
            <template #trailing>
                <UIcon name="i-heroicons-cloud-arrow-up" class="w-5 h-5" />
            </template>
        </UButton>
        <input ref="fileInput" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" type="file"
            name="fileUpload" id="fileUpload" @change="handleFileChange" />
    </div>
</template>

<script setup lang="ts">
const emit = defineEmits(['change'])
const fileInput = ref(null)

const triggerFileInput = () => {
    fileInput.value.click()
}

const handleFileChange = (event) => {
    emit('change', event)
}

defineProps<{
    label: string
}>()

</script>

<style>

</style>