<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 2: Select an Analysis Method</h1>
    </div>
    <h1 v-if="analysisStatus === 'pending'">Loading</h1>
    <div v-else class="select-container">
        <USelect v-model="pipelineStore.selectedMethod" :options="analysisMethods ?? []" option-attribute="display_name"
            valueAttribute="name" style="margin-bottom: 1%" @change="getParams" />
    </div>
</template>

<script setup lang="ts">
import type { PipelineAnalysesMethod, PipelineParams, PipelineStatus, FormState } from '~/types'

const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const { data: analysisMethods, status: analysisStatus } = await useFetch<PipelineAnalysesMethod[]>(`${runtimeConfig.public.baseURL}/api/analysis`)

async function getStatus() {
    pipelineStore.pipelineStatus = await $fetch<PipelineStatus>(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)
}

async function getParams() {
    await updateFormForMethod(pipelineStore.selectedMethod);
    await getStatus();
}

async function updateFormForMethod(method: string) {
    try {
        const data  = await $fetch<PipelineParams>(`${runtimeConfig.public.baseURL}/api/${method}/params`);

        if (data) {
            pipelineStore.globalParams = data.global_params || [];
            pipelineStore.methodSpecificParams = data.method_specific_params || [];
            initializeFormState();
        }
    } catch (error) {
        console.error('Error fetching parameters for method:', error);
    }
}

function initializeFormState() {
    pipelineStore.formState = {} as FormState;

    if (pipelineStore.pipelineStatus?.pipeline_params) {
        Object.entries(pipelineStore.pipelineStatus.pipeline_params).forEach(([key, value]) => {
            if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' || Array.isArray(value) || value === null) {
                pipelineStore.formState[key] = value;
            } else {
                // console.warn(`Unexpected type for HEY HEY ${key}:`, value);
            }
        });
    }

    const globalParams = pipelineStore.globalParams || [];
    const methodSpecificParams = pipelineStore.methodSpecificParams || [];
    const allParams = [...globalParams, ...methodSpecificParams];

    allParams.forEach(field => {
        if (typeof field === 'object' && field !== null && 'name' in field) {
            if (field.name === 'input_label' && pipelineStore.selectedMethod !== '_inputs') {
                pipelineStore.formState[field.name] = ["null"];
            } else if ('is_list' in field && field.is_list) {
                pipelineStore.formState[field.name] = Array.isArray(field.default) ? field.default : [];
            } else {
                pipelineStore.formState[field.name] = field.default !== undefined ? field.default : null;
            }
        } else {
            console.warn('Invalid field object:', field);
        }
    });
}

onMounted(() => {
    if (pipelineStore.parameters) {
        pipelineStore.globalParams = pipelineStore.parameters.global_params || [];
        pipelineStore.methodSpecificParams = pipelineStore.parameters.method_specific_params || [];
        initializeFormState();
    }
});

onMounted(async () => {
    if (pipelineStore.selectedMethod) {
        await updateFormForMethod(pipelineStore.selectedMethod);
    }
});

watch(() => pipelineStore.selectedMethod, async (newMethod) => {
    if (newMethod) {
        await updateFormForMethod(newMethod);
    }
});

watch(() => pipelineStore.pipelineStatus?.pipeline_params, (newParams) => {
    if (newParams) {
        Object.entries(newParams).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                pipelineStore.formState[key] = value.join(', ');
            } else if (value && typeof value === 'object') {
                pipelineStore.formState[key] = JSON.stringify(value); 
            } else if (typeof value === 'string' || typeof value === 'number') {
                pipelineStore.formState[key] = value;
            } else {
                console.warn(`Unexpected type for ${key}:`, value);
            }
        });
    }
}, { deep: true, immediate: true });

</script>

<style scoped></style>