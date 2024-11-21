<template>
    <div class="step-box">
        <div style="display: flex;">
            <h1 class="text-3xl">Step 1: Upload your files</h1>
            <UPopover mode="hover" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-6 h-6" />
                <template #panel>
                    <div class="p-4" style="text-align: left;">
                        <p>After uploading the file(s) you can</p>
                        <p>delete them manually. </p>
                        <p>Otherwise the files will be deleted</p> 
                        <p>automatically after {{ (configStore.config?.pipeline_ticket_expire_time_sec ?? 86400) /
                            3600}} hours.</p>
                    </div>
                </template>
            </UPopover>
        </div>
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
                    {{ configStore.config?.terms_and_conditions }}
                </div>
            </div>
        </UModal>
    </div>
    <div v-if="hasInputFiles">
        <p> Uploaded Files </p>
        <p v-for="item in pipelineStore.pipelineStatus?.pipeline_input_file_names" key="item">{{ item }}</p>
    </div>
</template>

<script setup lang="ts">
import type { PipelineStatus } from '~/types';

const configStore = useConfigStore()
const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const acceptAGB = ref(false)
const showAGBModal = ref(false)

const hasInputFiles = computed(() =>
    (pipelineStore.pipelineStatus?.pipeline_input_file_names?.length ?? 0) > 0
)

watch(() => pipelineStore.pipelineStatus?.pipeline_input_file_names, (newValue) => {
    acceptAGB.value = (newValue?.length ?? 0) > 0
}, { immediate: true })

const inputLabel = computed(() => {
    if ((pipelineStore.pipelineStatus?.pipeline_input_file_names?.length ?? 0) > 0) {
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
    const status = await $fetch<PipelineStatus>(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)
    pipelineStore.pipelineStatus = status
}

</script>

<style scoped></style>