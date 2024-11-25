<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 1: Select an Analysis Method</h1>
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
const runtimeConfig = useRuntimeConfig()

const visibleGlobalParams = computed(() =>
    pipelineStore.globalParams?.filter(f => f != null && f.type !== 'file') || []
)
const visibleMethodSpecificParams = computed(() =>
    pipelineStore.methodSpecificParams?.filter(f => f != null && f.type !== 'file') || []
)

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
        const data = await $fetch<PipelineParams>(`${runtimeConfig.public.baseURL}/api/${method}/params`);

        if (data) {
            pipelineStore.globalParams = data.global_params || [];
            pipelineStore.methodSpecificParams = data.method_specific_params || [];
        }
    } catch (error) {
        console.error('Error fetching parameters for method:', error);
    }
}

function initializeFormState() {
    pipelineStore.formState = {};

    if (pipelineStore.pipelineStatus?.pipeline_params) {
        const { global_params, method_specific_params } = pipelineStore.pipelineStatus.pipeline_params;
        Object.assign(pipelineStore.formState, global_params, method_specific_params);
    }

    const allParams = [...visibleGlobalParams.value, ...visibleMethodSpecificParams.value];

    allParams.forEach(field => {
        if (!(field.name in pipelineStore.formState)) {
            if (field.name === 'input_label' && pipelineStore.selectedMethod !== 'multiple_inputs') {
                pipelineStore.formState[field.name] = ["null"];
            } else if (field.is_list) {
                pipelineStore.formState[field.name] = Array.isArray(field.default) ? field.default : [];
            } else {
                pipelineStore.formState[field.name] = field.default !== undefined ? field.default : null;
            }
        }
    });
}

async function fetchStatusAndInitialize() {
    await getStatus();
    initializeFormState();
}

onMounted(async () => {
    await fetchStatusAndInitialize();
    if (pipelineStore.selectedMethod) {
        await updateFormForMethod(pipelineStore.selectedMethod);
    }
});

onMounted(() => {
    if (pipelineStore.parameters) {
        pipelineStore.globalParams = pipelineStore.parameters.global_params || [];
        pipelineStore.methodSpecificParams = pipelineStore.parameters.method_specific_params || [];
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