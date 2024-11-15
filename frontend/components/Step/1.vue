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
        <UCheckbox label="Accept the AGB" v-model="acceptAGB" required :disabled="acceptAGB" />
    </div>
    <div v-if="pipelineStatus?.pipeline_input_file_names?.length > 0">
        <p> Uploaded Files </p>
        <p v-for="item in pipelineStatus?.pipeline_input_file_names" key="item">{{ item }}</p>
    </div>
</template>

<script setup lang="ts">

const route = useRoute()
const ticket_id = route.params.id

const runtimeConfig = useRuntimeConfig();

const { data: pipelineStatus, error: statusError } = await useFetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/status`)

const acceptAGB = ref(false)



watch(() => pipelineStatus.value?.pipeline_input_file_names, (newValue) => {
    acceptAGB.value = newValue?.length > 0
}, { immediate: true })

const inputLabel = computed(() => {
    if (pipelineStatus.value?.pipeline_input_file_names?.length > 0) {
        return "Add an additional File"
    } else {
        return "Select your File"
    }
})

function uncheckedAGB() {
    alert("To upload files you must accept the AGBs")
}

const formDataCheck = ref(false)


async function printUploadChange(event: Event) {
    const input = event.target as HTMLInputElement

    if (input.files && input.files.length > 0) {
        const formData = new FormData()
        formData.append('file', input.files[0])
        formDataCheck.value = true

        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/upload`, {
            method: 'POST',
            body: formData,
        })
    }
    const status = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/status`)
    pipelineStatus.value = status
}

</script>

<style scoped></style>