<template>
    <div class="step-box">
        <h1 class="text-3xl">Step 3: (Optional) Pipeline Parameters</h1>
    </div>
    <div style="text-align: left">
        <UAccordion
            v-if="(pipelineStore?.globalParams && typeof pipelineStore.globalParams === 'object' && Object.keys(pipelineStore.globalParams).length > 0) ||
                (pipelineStore?.methodSpecificParams && typeof pipelineStore.methodSpecificParams === 'object' && Object.keys(pipelineStore.methodSpecificParams).length > 0)"
            :items="accordionItems">
            <template #item="{ item }">
                <div
                    style="border: solid; border-color: #d3f4e1; border-radius: 1%; padding: 2%; background-color: #f6fdf9;">
                    <UForm :state="pipelineStore.formState">
                        <div v-for="field in pipelineStore?.globalParams?.filter(f => f != null)" :key="field.name">
                            <UFormGroup
                                v-if="field.name !== 'input_label' || pipelineStore.selectedMethod === 'multiple_inputs'"
                                :label="formatLabel(field.name)" :required="field.required">

                                <UInput v-if="['str', 'int', 'float'].includes(field.type) && !field.is_list"
                                    v-model="pipelineStore.formState[field.name]"
                                    :placeholder="field.default?.toString() || ''" :type="getInputType(field.type)"
                                    @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <UInput v-else-if="['str', 'int', 'float'].includes(field.type) && field.is_list"
                                    v-model="pipelineStore.formState[field.name]"
                                    placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <UToggle v-else-if="field.type === 'bool'" v-model="pipelineStore.formState[field.name]"
                                    @blur="handleBlur(field.name)" />

                                <UTextarea v-else-if="field.type === 'List'"
                                    v-model="pipelineStore.formState[field.name]"
                                    placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <div v-if="pipelineStore.formState[`${field.name}_error`]">
                                    <span style="color: red;">{{ pipelineStore.formState[`${field.name}_error`]
                                        }}</span>
                                </div>
                            </UFormGroup>
                        </div>

                        <div v-for="field in pipelineStore?.methodSpecificParams?.filter(f => f != null)"
                            :key="field.name">
                            <UFormGroup
                                v-if="field.name !== 'input_label' || pipelineStore.selectedMethod === 'multiple_inputs'"
                                :label="formatLabel(field.name)" :required="field.required">

                                <UInput v-if="['str', 'int', 'float'].includes(field.type) && !field.is_list"
                                    v-model="pipelineStore.formState[field.name]"
                                    :placeholder="field.default?.toString() || ''" :type="getInputType(field.type)"
                                    @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <UInput v-else-if="['str', 'int', 'float'].includes(field.type) && field.is_list"
                                    v-model="pipelineStore.formState[field.name]"
                                    placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <UToggle v-else-if="field.type === 'bool'" v-model="pipelineStore.formState[field.name]"
                                    @blur="handleBlur(field.name)" />

                                <UTextarea v-else-if="field.type === 'List'"
                                    v-model="pipelineStore.formState[field.name]"
                                    placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                    :color="pipelineStore.formState[`${field.name}_error`] ? 'red' : undefined" />

                                <div v-if="pipelineStore.formState[`${field.name}_error`]">
                                    <span style="color: red;">{{ pipelineStore.formState[`${field.name}_error`]
                                        }}</span>
                                </div>
                            </UFormGroup>
                        </div>
                    </UForm>
                </div>
            </template>
        </UAccordion>
    </div>
</template>

<script setup lang="ts">

const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();

async function handleBlur(fieldName: string) {
    const allParams = [...pipelineStore.globalParams, ...pipelineStore.methodSpecificParams];
    const field = allParams.find(f => f.name === fieldName);

    pipelineStore.formState[`${fieldName}_error`] = null;

    if (fieldName === 'input_label' && pipelineStore.selectedMethod !== 'multiple_inputs') {
        pipelineStore.formState[fieldName] = ["null"];
        return;
    }

    if (field.is_list && typeof pipelineStore.formState[fieldName] === 'string') {
        pipelineStore.formState[fieldName] = pipelineStore.formState[fieldName].split(',').map(item => item.trim()).filter(Boolean);
    }

    const missingFields = allParams.filter(field => {
        if (field.required) {
            if (field.type === 'bool') {
                return pipelineStore.formState[field.name] === undefined;
            } else if (field.is_list) {
                return Array.isArray(pipelineStore.formState[field.name]) && pipelineStore.formState[field.name].length === 0;
            } else {
                return !pipelineStore.formState[field.name] && pipelineStore.formState[field.name] !== false;
            }
        }
        return false;
    });

    missingFields.forEach(field => {
        pipelineStore.formState[`${field.name}_error`] = `${formatLabel(field.name)} cannot be empty`;
    });

    const valueToSend = pipelineStore.formState[fieldName];

    try {
        const url = `${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}`;
        const isGlobalParam = pipelineStore.globalParams.some(param => param.name === fieldName);
        const body = {
            global_params: {},
            method_specific_params: {}
        };

        if (isGlobalParam) {
            body.global_params[fieldName] = valueToSend;
        } else {
            body.method_specific_params[fieldName] = valueToSend;
        }

        await $fetch(url, { method: "PATCH", body: body });
        await getStatus();
    } catch (error) {
        console.error(`Error updating field ${fieldName}:`, error);
        pipelineStore.formState[`${fieldName}_error`] = `Failed to update ${formatLabel(fieldName)}. Please try again.`;
    }
}

function formatLabel(key: string): string {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getInputType(fieldType: string): string {
    switch (fieldType) {
        case 'int':
            return 'number';
        case 'float':
            return 'number';
        default:
            return 'text';
    }
}

async function getStatus() {
    pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/status`)
}

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

const accordionItems = ref([
    {
        label: 'Pipeline Parameter Setting',
        content: 'Form will be rendered here'
    }
]);

</script>

<style scoped></style>