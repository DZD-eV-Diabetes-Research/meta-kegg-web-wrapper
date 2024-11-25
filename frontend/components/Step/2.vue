<template>
    <div class="step-box">
        <div style="display: flex;">
            <h1 class="text-3xl">Step 2: Upload your files</h1>
            <UPopover mode="hover" :popper="{ placement: 'right' }">
                <UIcon name="i-heroicons-question-mark-circle" class="w-6 h-6" />
                <template #panel>
                    <div class="p-4" style="text-align: left;">
                        <p>After uploading the file(s) you can</p>
                        <p>delete them manually. </p>
                        <p>Otherwise the files will be deleted</p>
                        <p>automatically after {{ (configStore.config?.pipeline_ticket_expire_time_sec ?? 86400) /
                            3600 }} hours.</p>
                    </div>
                </template>
            </UPopover>
        </div>
    </div>
    <div v-if="acceptAGB" class="input-field-container">
        <UICustomInputField @input="printUploadChange" :label="inputLabel" name="input_file_path" />
        <UICustomInputField v-for="button in fileButtons" :key="button.name" @input="printUploadChange" :name="button.name" :label="formatButtonLabel(button.name)" />
    </div>
    <div v-else style="margin-top: 1%; margin-bottom: 0.5%">
        <UButton label="Select your File" variant="outline" @click="uncheckedAGB" style="margin: 0% 1%;">
            <template #trailing>
                <UIcon name="i-heroicons-cloud-arrow-up" class="w-5 h-5" />
            </template>
        </UButton>
        <UButton v-for="button in fileButtons" :key="button.name" variant="outline" :label="formatButtonLabel(button.name)" @click="uncheckedAGB" style="margin: 0% 1%;">
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
    <div>
        <p v-if="pipelineStore.pipelineStatus?.pipeline_input_file_names?.input_file_path.length > 0" class="text-lg" style="margin-top: 1%; text-align: center;">Uploaded Files</p>
        <div v-for="(value, key) in pipelineStore.pipelineStatus?.pipeline_input_file_names" :key="key">
            <p v-if="key === 'input_file_path' && value.length > 0"></p>
            <p v-if="key === 'methylation_file_path' && value.length > 0" class="text-lg" style="margin-top: 1%; text-align: center;">Methylation
                Files</p>
            <p v-if="key === 'miRNA_file_path' && value.length > 0" class="text-lg" style="margin-top: 1%; text-align: center;">
                miRNA Files</p>
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div v-for="item in value" :key="item" style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <p class="text-base" style="margin-right: 0.5rem;">{{ item }}</p>
                    <UButton variant="link" color="red" :padded="true" @click="deleteFile(item, key)">
                        <UIcon name="i-heroicons-trash" class="w-5 h-5" />
                    </UButton>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { PipelineStatus } from '~/types';

const configStore = useConfigStore()
const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const acceptAGB = ref(false)
const showAGBModal = ref(false)

onMounted(() => {
    const pipelineInputFileNames = pipelineStore.pipelineStatus?.pipeline_input_file_names
    acceptAGB.value = (pipelineInputFileNames && Object.keys(pipelineInputFileNames).length > 0) ||
        (Array.isArray(pipelineInputFileNames) && pipelineInputFileNames.length > 0)
})

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

async function printUploadChange(event: Event, file_name: string) {
    const input = event.target as HTMLInputElement

    if (input.files && input.files.length > 0) {
        const formData = new FormData()
        formData.append('file', input.files[0])

        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/file/upload/${file_name}`, {
            method: 'POST',
            body: formData,
        })
        input.value = ''
    }
    const status = await $fetch<PipelineStatus>(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)
    pipelineStore.pipelineStatus = status

    nextTick(() => {
        console.log('All files uploaded:', allFilesUploaded.value)
    })
}

async function deleteFile(fileName: string, file_path: string) {
    await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/file/remove/${file_path}/${fileName}`, {
        method: 'DELETE',
    })

    const fileInputs = document.querySelectorAll('input[type="file"]')
    fileInputs.forEach(input => {
        (input as HTMLInputElement).value = ''
    })

    pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)

    nextTick(() => {
        console.log('All files uploaded:', allFilesUploaded.value)
    })
}

const fileButtons = computed(() =>
    pipelineStore.methodSpecificParams?.filter((element) => element.type === 'file') || []
)

const formatButtonLabel = (name: string) => {
    return name.split('_')[0].charAt(0).toUpperCase() + name.split('_')[0].slice(1) + ' File'
}

const allFilesUploaded = computed(() => {
    const inputFileNames = pipelineStore.pipelineStatus?.pipeline_input_file_names
    const hasInputFile = inputFileNames?.input_file_path?.length > 0
    const allMethodSpecificFilesUploaded = fileButtons.value.every(button =>
        (inputFileNames?.[button.name]?.length ?? 0) > 0
    )

    pipelineStore.uploadCheck = !(hasInputFile && allMethodSpecificFilesUploaded)
    return !(hasInputFile && allMethodSpecificFilesUploaded)
})

</script>

<style scoped>
.input-field-container {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 1%;
    margin-bottom: 0.5%;
}
</style>