<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 1: Upload your files</h1>
    </div>
    <div v-if="acceptAGB" style="margin-top: 1%; margin-bottom: 0.5%">
        <UICustomInputField @change="printUploadChange" :label="inputLabel" />
    </div>
    <div v-else style="margin-top: 1%; margin-bottom: 0.5%">
        <UButton label="Select your File" variant="outline" @click="uncheckedAGB">
            <template #trailing>
                <UIcon name="i-heroicons-cloud-arrow-up" class="w-5 h-5" />
            </template>
        </UButton>
    </div>
    <div style="display: flex; justify-content: center; margin-bottom: 0.5%;">
        <UCheckbox v-model="acceptAGB" :disabled="acceptAGB" />
        <label for="acceptAGB" style="padding-left: 0.5%; padding-right: 0.25%">Accept the </label>
        <UButton variant="link" size="xl" :padded="false" @click="showAGBModal = true">AGB</UButton>
        <UModal v-model="showAGBModal">
            <div class="p-4">
                <div style="text-align: center;">
                    {{ config.terms_and_conditions }}
                </div>
            </div>
        </UModal>
    </div>
    <div v-if="pipelineStore.pipelineStatus?.pipeline_input_file_names?.length > 0">
        <p> Uploaded Files </p>
        <p v-for="item in pipelineStore.pipelineStatus?.pipeline_input_file_names" key="item">{{ item }}</p>
    </div>
</template>

<script setup lang="ts">

const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const acceptAGB = ref(false)
const showAGBModal = ref(false)
const { data: config } = await useFetch(`${runtimeConfig.public.baseURL}/config`)


watch(() => pipelineStore.pipelineStatus?.pipeline_input_file_names, (newValue) => {
    acceptAGB.value = newValue?.length > 0
}, { immediate: true })

const inputLabel = computed(() => {
    if (pipelineStore.pipelineStatus?.pipeline_input_file_names?.length > 0) {
        return "Add an additional File"
    } else {
        return "Select your File"
    }
})

function uncheckedAGB() {
    alert("To upload files you must accept the AGBs")
}

async function printUploadChange(event: Event) {
    const input = event.target as HTMLInputElement

    if (input.files && input.files.length > 0) {
        const formData = new FormData()
        formData.append('file', input.files[0])
        pipelineStore.uploadCheck = true

        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/upload`, {
            method: 'POST',
            body: formData,
        })
    }
    const status = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)
    pipelineStore.pipelineStatus = status
}

</script>

<style scoped></style>