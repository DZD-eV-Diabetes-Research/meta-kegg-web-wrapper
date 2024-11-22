<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 4: Start the Pipeline</h1>
    </div>
    <UButton @click="startPipeline">Start run</UButton>
    <div style="margin: 1%;" v-if="pipelineStore.uploadErrorMessage" class="submit-error-message">
            <h1 class="text-2xl">{{ pipelineStore.uploadErrorMessage }}</h1>
        </div>
    <div style="margin: 1%;" v-if="pipelineStore.requiredFieldsError" class="submit-error-message">
            <h1 class="text-2xl">{{ pipelineStore.requiredFieldsError }}</h1>
        </div>
</template>

<script setup lang="ts">
const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();

const downloadStatus = ref(false)
const isMaxPlaceSet = ref(false)

async function startPipeline() {

    pipelineStore.pipeLineProgress = 0
    pipelineStore.maxPlace = null
    downloadStatus.value = false
    pipelineStore.pipelineStart = true
    pipelineStore.isLoading = true
    isMaxPlaceSet.value = false
    pipelineStore.uploadErrorMessage = ""
    pipelineStore.requiredFieldsError = ""
    

    if (!pipelineStore.uploadCheck) {
        console.log(pipelineStore.uploadErrorMessage);
        pipelineStore.uploadErrorMessage = "You need to upload all required file(s)"
        console.log(pipelineStore.uploadErrorMessage);
        pipelineStore.isLoading = false
        pipelineStore.pipelineStart = false
        return
    }

    if (!checkRequiredFields()) {

        pipelineStore.isLoading = false
        pipelineStore.pipelineStart = false
        return
    }

    try {
        pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/run/${pipelineStore.selectedMethod}`, {
            method: "POST"
        })

        if (pipelineStore?.pipelineStatus?.place_in_queue) {

            if (!isMaxPlaceSet.value) {
                pipelineStore.maxPlace = pipelineStore.pipelineStatus.place_in_queue
                isMaxPlaceSet.value = true
            }

            pipelineStore.pipeLineProgress = Math.round(100 * ((pipelineStore.pipelineStatus.place_in_queue / pipelineStore.maxPlace!)))
        }

        await getStatus()

        while (pipelineStore?.pipelineStatus?.state !== 'success' && pipelineStore?.pipelineStatus?.state !== 'failed') {
            await new Promise(resolve => setTimeout(resolve, 5000))
            await getStatus()
        }

        if (pipelineStore.pipelineStatus.state === 'success') {
            downloadStatus.value = true
        }

        if (pipelineStore.pipelineStatus.error) {
            pipelineStore.errorMessage = pipelineStore.pipelineStatus.error
            pipelineStore.errorStack = pipelineStore?.pipelineStatus?.error_traceback?.replace(/\n/g, `<br>`) ?? ""
        }


    } catch (error) {
        console.error('Error in pipeline:', error)
    } finally {
        pipelineStore.isLoading = false
        pipelineStore.pipelineStart = false
    }
}

async function getStatus() {
    pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`);

    if (pipelineStore?.pipelineStatus?.place_in_queue) {
        pipelineStore.pipeLineProgress = Math.round(100 * (pipelineStore.pipelineStatus.place_in_queue / pipelineStore.maxPlace!));
    }

    if (pipelineStore.pipelineStatus) {
        pipelineStore.errorMessage = pipelineStore.pipelineStatus.error ?? ""; 
        pipelineStore.errorStack = pipelineStore.pipelineStatus.error_traceback ?? ""; 
    }
}


function checkRequiredFields() {
    const allParams = [...pipelineStore.globalParams, ...pipelineStore.methodSpecificParams];
    const fileFields = ['input_file_path', 'methylation_path', 'miRNA_path'];
    
    const emptyRequiredFields = allParams.filter(field => {
        if (field.required && !fileFields.includes(field.name)) {
            if (field.type === 'bool') {
                return pipelineStore.formState[field.name] === undefined;
            } else if (field.is_list) {
                return Array.isArray(pipelineStore.formState[field.name]) && pipelineStore?.formState[field.name]?.length === 0;
            } else {
                return !pipelineStore.formState[field.name] && pipelineStore.formState[field.name] !== false;
            }
        }
        return false;
    });    

    if (emptyRequiredFields.length > 0) {        
        pipelineStore.requiredFieldsError = `${emptyRequiredFields.length} required field(s) cannot be empty when submitting the form.`;
        return false;
    }

    pipelineStore.requiredFieldsError = '';
    return true;
}

// watch(() => pipelineStore.pipelineStatus?.pipeline_input_file_names, (newValue) => {
//     if (newValue && newValue.length > 0) {
//         pipelineStore.uploadCheck  = true
//     } else {
//         pipelineStore.uploadCheck  = false
//     }
// }, { deep: true, immediate: true })


watch(() => pipelineStore.selectedMethod, (newMethod) => {
    if (newMethod !== 'multiple_inputs') {
        pipelineStore.formState.input_label = ["null"];
    } else {
        const inputLabelField = pipelineStore.globalParams.find(param => param.name === 'input_label');
        if (!pipelineStore.formState.hasOwnProperty('input_label') ||
            (Array.isArray(pipelineStore.formState.input_label) && pipelineStore.formState.input_label[0] === "null")) {
                pipelineStore.formState.input_label = inputLabelField?.default || [];
        }
    }
});

</script>

<style scoped>
.error-message {
    color: red;
    font-size: 1.5rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

.submit-error-message {
    color: red;
    margin-bottom: 0.5rem;
    margin-top: 0.5rem;
    font-weight: bold;
}
</style>