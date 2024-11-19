<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 2: Select an Analysis Method</h1>
    </div>
    <h1 v-if="analysisStatus === 'pending'">Loading</h1>
    <div v-else class="select-container">
        <USelect v-model="pipelineStore.selectedMethod" :options="analysisMethods" option-attribute="display_name"
            valueAttribute="name" style="margin-bottom: 1%" @change="getParams" />
    </div>
</template>

<script setup lang="ts">
const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const { data: analysisMethods, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)

async function getParams() {
    await updateFormForMethod(pipelineStore.selectedMethod);
    await getStatus();
}

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

async function updateFormForMethod(method) {
    try {
        const { data } = await useFetch(`${runtimeConfig.public.baseURL}/api/${method}/params`);

        if (data.value) {
            pipelineStore.globalParams = data.value.global_params || [];
            pipelineStore.methodSpecificParams = data.value.method_specific_params || [];
            initializeFormState();
        }
    } catch (error) {
        console.error('Error fetching parameters for method:', error);
    }
}

async function getStatus() {
    pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/status`)
}


function initializeFormState() {
    pipelineStore.formState = {};

    if (pipelineStore.pipelineStatus && pipelineStore.pipelineStatus.pipeline_params) {
        Object.entries(pipelineStore.pipelineStatus.pipeline_params).forEach(([key, value]) => {
            pipelineStore.formState[key] = value;
        });
    }

    const allParams = [...pipelineStore.globalParams, ...pipelineStore.methodSpecificParams];
    allParams.forEach(field => {
        if (field.name === 'input_label' && pipelineStore.selectedMethod !== 'multiple_inputs') {
            pipelineStore.formState[field.name] = ["null"];
        } else if (field.is_list) {
            pipelineStore.formState[field.name] = field.default || [];
        } else {
            pipelineStore.formState[field.name] = field.default !== undefined ? field.default : null;
        }
    });
}

watch(() => pipelineStore.pipelineStatus?.pipeline_params, (newParams) => {
    if (newParams) {
        Object.entries(newParams).forEach(([key, value]) => {
            pipelineStore.formState[key] = value;
        });
    }
}, { deep: true, immediate: true });



onMounted(() => {
    if (pipelineStore.parameters) {
        pipelineStore.globalParams  = pipelineStore.parameters.global_params || [];
        pipelineStore.methodSpecificParams  = pipelineStore.parameters.method_specific_params || [];
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

</script>

<style scoped></style>