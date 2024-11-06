<template>
    <div class="relative">
        <UButton :label="label" color="primary" variant="outline">
            <template #trailing>
                <UIcon name="i-heroicons-cloud-arrow-up" class="w-5 h-5" />
            </template>
        </UButton>
        <input ref="fileInput" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" type="file"
            name="fileUpload" id="fileUpload" @change="handleFileChange" />
    </div>
</template>

<script setup lang="ts">

interface Props {
    label: string;
    checkAGB: boolean;
}

const props = defineProps<Props>()

const emit = defineEmits<{
    (e: 'change', event: Event): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)


const handleFileChange = (event: Event) => {
    emit('change', event)
}
</script>