<template>
    <div>
        <StaticIntroBox />
        <div v-if="healthFetchError || !healthStatus?.healthy">
            <UIBaseCard :narrow-width="true">
                <h1 class="text-3xl font-bold" style="color: red;">There seems to be an error with the server please try
                    again later</h1>
            </UIBaseCard>
        </div>
        <UIBaseCard v-if="statusError" :narrow-width="true">
            <div class="statusError">
                <h3 class="text-4xl">Your MetaKegg url could not be found</h3>
                <br>
                <h3 class="text-4xl">Maybe it has already expired</h3>
                <br>
                <h3 class="text-4xl">The current expiration time is: {{ config.pipeline_ticket_expire_time_sec / 3600 }}
                    hours</h3>
                <br>
                <UButton label="Create New Ticket ID" variant="outline" color="red" @click="newID" />
            </div>
        </UIBaseCard>
        <UIBaseCard v-else :narrow-width="true">
            <Step0 />
            <hr class="custom-hr">
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
                        <Placeholder class="h-48" />
                        <div style="text-align: center;">
                            {{ config.terms_and_conditions }}
                        </div>
                    </div>
                </UModal>
            </div>
            <div v-if="pipelineStatus?.pipeline_input_file_names?.length > 0">
                <p> Uploaded Files </p>
                <p v-for="item in pipelineStatus?.pipeline_input_file_names" key="item">{{ item }}</p>
            </div>
            <hr class="custom-hr">
            <div class="step-box">
                <h1 class="text-3xl">Step 2: Select an Analysis Method</h1>
            </div>
            <h1 v-if="analysisStatus === 'pending'">Loading</h1>
            <div v-else class="select-container">
                <USelect v-model="selectedMethod" :options="analysisMethods" option-attribute="display_name"
                    valueAttribute="name" style="margin-bottom: 1%" @change="getParams" />
            </div>
            <hr class="custom-hr">
            <div class="step-box">
                <h1 class="text-3xl">Step 3: (Optional) Pipeline Parameters</h1>
            </div>
            <div style="text-align: left">
                <UAccordion v-if="globalParams.length > 0 || methodSpecificParams.length > 0" :items="accordionItems">
                    <template #item="{ item }">
                        <div
                            style="border: solid; border-color: #d3f4e1; border-radius: 1%; padding: 2%; background-color: #f6fdf9;">
                            <UForm :state="formState">
                                <div v-for="field in globalParams" :key="field.name">
                                    <UFormGroup
                                        v-if="field.name !== 'input_label' || selectedMethod === 'multiple_inputs'"
                                        :label="formatLabel(field.name)" :required="field.required">

                                        <UInput v-if="['str', 'int', 'float'].includes(field.type) && !field.is_list"
                                            v-model="formState[field.name]"
                                            :placeholder="field.default?.toString() || ''"
                                            :type="getInputType(field.type)" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <UInput
                                            v-else-if="['str', 'int', 'float'].includes(field.type) && field.is_list"
                                            v-model="formState[field.name]"
                                            placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <UToggle v-else-if="field.type === 'bool'" v-model="formState[field.name]"
                                            @blur="handleBlur(field.name)" />

                                        <UTextarea v-else-if="field.type === 'List'" v-model="formState[field.name]"
                                            placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <div v-if="formState[`${field.name}_error`]">
                                            <span style="color: red;">{{ formState[`${field.name}_error`] }}</span>
                                        </div>
                                    </UFormGroup>
                                </div>
                                <div v-for="field in methodSpecificParams" :key="field.name">
                                    <UFormGroup
                                        v-if="field.name !== 'input_label' || selectedMethod === 'multiple_inputs'"
                                        :label="formatLabel(field.name)" :required="field.required">

                                        <UInput v-if="['str', 'int', 'float'].includes(field.type) && !field.is_list"
                                            v-model="formState[field.name]"
                                            :placeholder="field.default?.toString() || ''"
                                            :type="getInputType(field.type)" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <UInput
                                            v-else-if="['str', 'int', 'float'].includes(field.type) && field.is_list"
                                            v-model="formState[field.name]"
                                            placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <UToggle v-else-if="field.type === 'bool'" v-model="formState[field.name]"
                                            @blur="handleBlur(field.name)" />

                                        <UTextarea v-else-if="field.type === 'List'" v-model="formState[field.name]"
                                            placeholder="Enter items separated by commas" @blur="handleBlur(field.name)"
                                            :color="formState[`${field.name}_error`] ? 'red' : undefined" />

                                        <div v-if="formState[`${field.name}_error`]">
                                            <span style="color: red;">{{ formState[`${field.name}_error`] }}</span>
                                        </div>
                                    </UFormGroup>
                                </div>
                            </UForm>
                        </div>
                    </template>
                </UAccordion>
            </div>
            <hr class="custom-hr">
            <div class="step-box">
                <h1 class="text-3xl">Step 4: Start the Pipeline</h1>
            </div>
            <div v-if="requiredFieldsError" class="submit-error-message">
                {{ requiredFieldsError }}
            </div>
            <UButton @click="startPipeline">Start run</UButton>
            <hr class="custom-hr">
            <div class="step-box">
                <h1 class="text-3xl">Step 5: Download your File</h1>
            </div>
            <div v-if="!errorMessage">
                <div v-if="pipelineStatus?.state === 'queued'">
                    <div style="margin: 2% 0%;">
                        <p>We are currently experiencing a high number of requests. You are placed in a queue, please be patient.</p>
                        <UProgress :value="pipeLineProgress" />
                        <div style="text-align: right; color: #31c363;">
                            <p>Your current place is {{ pipelineStatus?.place_in_queue }} out of {{ maxPlace }}</p>
                        </div>
                    </div>
                </div>
                <div v-else-if="isLoading && pipelineStart && pipelineStatus?.state === 'running'">
                    <p style="margin-bottom: 0.5%;">The monkeys are busy in the background please be patient</p>
                    <UProgress animation="carousel" />
                </div>
                <div v-else-if="!isLoading && pipelineStatus?.state === 'success'">
                    <UButton @click="downloadFile" variant="outline" label="Your File">
                        <template #trailing>
                            <UIcon name="i-heroicons-cloud-arrow-down" class="w-5 h-5" />
                        </template>
                    </UButton>
                </div>
            </div>
            <div v-else>
                <h1 class="text-3xl font-bold" style="color: red; margin: 1% 0%">There seems to be an error: {{
                    errorMessage }}
                </h1>
                <UAccordion v-if="errorMessageDetail" variant="outline" size="xl" color="red"
                    :items="[{ label: 'Detailed error', content: `${errorMessageDetail}` }]">
                    <template #item="{ item }">
                        <div style="text-align: left;">
                            <p style="color: red;" v-html="item.content" />
                            <br>
                            <div
                                style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%;">
                                <div style="border: solid 1px; padding: 10px;">
                                    <a class="text-3xl"
                                        href="mailto:{{ config.bug_report_email }}?subject='Error Metakegg'&body='{{ item.content }}'">
                                        Send a mail to our support
                                        <UIcon name="i-heroicons-paper-airplane" class="w-5 h-5" />
                                    </a>
                                </div>
                            </div>
                        </div>
                    </template>
                </UAccordion>
            </div>
        </UIBaseCard>
    </div>
</template>

<script setup lang="ts">

const route = useRoute()

const pipeLineProgress = ref(0)

const runtimeConfig = useRuntimeConfig();

interface HealthStatus {
    healthy: boolean,
    dependencies: []
}

interface AnalysisMethods {
    name: string,
    display_name: string,
    internal_id: number,
    desc: string
}

const showAGBModal = ref(false)


const ticket_id = route.params.id

const selectedMethod = ref("single_input_genes")

const { data: pipelineStatus, error: statusError } = await useFetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/status`)
const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: config } = await useFetch(`${runtimeConfig.public.baseURL}/config`)
const { data: parameters } = await useFetch(`${runtimeConfig.public.baseURL}/api/${selectedMethod.value}/params`)

const { data: analysisMethods, error: analysisMethodsError, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)

const acceptAGB = ref(false)

watch(() => pipelineStatus.value?.pipeline_input_file_names, (newValue) => {
    acceptAGB.value = newValue?.length > 0
}, { immediate: true })

const formDataCheck = ref(false)

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

const errorMessage = ref("")
const errorMessageDetail = ref("")

const isLoading = ref(false)
const pipelineStart = ref(false)
const downloadStatus = ref(false)

const requiredFieldsError = ref('')

function checkRequiredFields() {
    const allParams = [...globalParams.value, ...methodSpecificParams.value];
    const emptyRequiredFields = allParams.filter(field => {
        if (field.required) {
            if (field.type === 'bool') {
                return formState.value[field.name] === undefined;
            } else if (field.is_list) {
                return Array.isArray(formState.value[field.name]) && formState.value[field.name].length === 0;
            } else {
                return !formState.value[field.name] && formState.value[field.name] !== false;
            }
        }
        return false;
    });

    if (emptyRequiredFields.length > 0) {
        requiredFieldsError.value = `${emptyRequiredFields.length} required field(s) cannot be empty when submitting the form.`;
        return false;
    }

    requiredFieldsError.value = '';
    return true;
}

async function startPipeline() {
    downloadStatus.value = false
    pipelineStart.value = true
    isLoading.value = true
    errorMessage.value = ""
    errorMessageDetail.value = ""
    requiredFieldsError.value = ""

    if (formDataCheck.value === false) {
        errorMessage.value = "You need to upload a file"
        isLoading.value = false
        pipelineStart.value = false
        return
    }

    if (!checkRequiredFields()) {
        isLoading.value = false
        pipelineStart.value = false
        return
    }

    try {
        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/run/${selectedMethod.value}`, {
            method: "POST"
        })
        await getStatus()

        while (pipelineStatus.value.state !== 'success' && pipelineStatus.value.state !== 'failed') {
            await new Promise(resolve => setTimeout(resolve, 5000))
            await getStatus()
        }

        if (pipelineStatus.value.state === 'success') {
            downloadStatus.value = true
        }

        if (pipelineStatus.value.error) {
            errorMessage.value = pipelineStatus.value.error
            errorMessageDetail.value = pipelineStatus.value.error_traceback.replace(/\n/g, `<br>`)
        }


    } catch (error) {
        console.error('Error in pipeline:', error)
    } finally {
        isLoading.value = false
        pipelineStart.value = false
    }
}

const maxPlace = ref()
const isMaxPlaceSet = ref(false)

async function getStatus() {
    pipelineStatus.value = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/status`)

    if (pipelineStatus.value.place_in_queue) {
        if (!isMaxPlaceSet.value) {
            maxPlace.value = pipelineStatus.value.place_in_queue
            isMaxPlaceSet.value = true
        }
        pipeLineProgress.value = Math.round(100 * (1 - (pipelineStatus.value.place_in_queue / maxPlace.value)))
    }
}


const accordionItems = ref([
    {
        label: 'Pipeline Parameter Setting',
        content: 'Form will be rendered here'
    }
]);

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


const globalParams = ref([])
const methodSpecificParams = ref([]);

const formState = ref({});

onMounted(() => {
    if (parameters.value) {
        globalParams.value = parameters.value.global_params || [];
        methodSpecificParams.value = parameters.value.method_specific_params || [];
        initializeFormState();
    }
});

onMounted(async () => {
    if (selectedMethod.value) {
        await updateFormForMethod(selectedMethod.value);
    }
});

watch(selectedMethod, async (newMethod) => {
    if (newMethod) {
        await updateFormForMethod(newMethod);
    }
});

async function updateFormForMethod(method) {
    try {
        const { data } = await useFetch(`${runtimeConfig.public.baseURL}/api/${method}/params`);

        if (data.value) {
            globalParams.value = data.value.global_params || [];
            methodSpecificParams.value = data.value.method_specific_params || [];
            initializeFormState();
        }
    } catch (error) {
        console.error('Error fetching parameters for method:', error);
    }
}

function initializeFormState() {
    formState.value = {};

    if (pipelineStatus.value && pipelineStatus.value.pipeline_params) {
        Object.entries(pipelineStatus.value.pipeline_params).forEach(([key, value]) => {
            formState.value[key] = value;
        });
    }

    const allParams = [...globalParams.value, ...methodSpecificParams.value];
    allParams.forEach(field => {
        if (field.name === 'input_label' && selectedMethod.value !== 'multiple_inputs') {
            formState.value[field.name] = ["null"];
        } else if (field.is_list) {
            formState.value[field.name] = field.default || [];
        } else {
            formState.value[field.name] = field.default !== undefined ? field.default : null;
        }
    });
}
watch(() => pipelineStatus.value?.pipeline_params, (newParams) => {
    if (newParams) {
        Object.entries(newParams).forEach(([key, value]) => {
            formState.value[key] = value;
        });
    }
}, { deep: true, immediate: true });

async function handleBlur(fieldName) {
    const allParams = [...globalParams.value, ...methodSpecificParams.value];
    const field = allParams.find(f => f.name === fieldName);

    formState.value[`${fieldName}_error`] = null;

    if (fieldName === 'input_label' && selectedMethod.value !== 'multiple_inputs') {
        formState.value[fieldName] = ["null"];
        return;
    }

    if (field.is_list && typeof formState.value[fieldName] === 'string') {
        formState.value[fieldName] = formState.value[fieldName].split(',').map(item => item.trim()).filter(Boolean);
    }

    const missingFields = allParams.filter(field => {
        if (field.required) {
            if (field.type === 'bool') {
                return formState.value[field.name] === undefined;
            } else if (field.is_list) {
                return Array.isArray(formState.value[field.name]) && formState.value[field.name].length === 0;
            } else {
                return !formState.value[field.name] && formState.value[field.name] !== false;
            }
        }
        return false;
    });

    missingFields.forEach(field => {
        formState.value[`${field.name}_error`] = `${formatLabel(field.name)} cannot be empty`;
    });

    const valueToSend = formState.value[fieldName];

    try {
        const url = `${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}`;
        const isGlobalParam = globalParams.value.some(param => param.name === fieldName);
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
        formState.value[`${fieldName}_error`] = `Failed to update ${formatLabel(fieldName)}. Please try again.`;
    }
}

watch(selectedMethod, (newMethod) => {
    if (newMethod !== 'multiple_inputs') {
        formState.value.input_label = ["null"];
    } else {
        const inputLabelField = globalParams.value.find(param => param.name === 'input_label');
        if (!formState.value.hasOwnProperty('input_label') ||
            (Array.isArray(formState.value.input_label) && formState.value.input_label[0] === "null")) {
            formState.value.input_label = inputLabelField?.default || [];
        }
    }
});
async function downloadFile() {
    try {
        const downloadedFile = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id}/result`)

        const blobUrl = URL.createObjectURL(downloadedFile);

        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = pipelineStatus.value.pipeline_output_zip_file_name + '.zip';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(blobUrl);
    } catch (error) {
        console.error('Download failed:', error);
    }
}

function newID() {
    navigateTo("/")
}

async function getParams() {
    await updateFormForMethod(selectedMethod.value);
    await getStatus();
}

watch(() => pipelineStatus.value?.pipeline_input_file_names, (newValue) => {
    if (newValue && newValue.length > 0) {
        formDataCheck.value = true
    } else {
        formDataCheck.value = false
    }
}, { deep: true, immediate: true })

</script>

<style>
.select-container {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

.select-container :deep(.u-select) {
    max-width: 25rem;
}

.step-box {
    margin-top: 2%;
    margin-bottom: 1%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.custom-hr {
    margin: 2% 0%;
}

.statusError {
    color: red;
}

.error-message {
    color: red;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.submit-error-message {
    color: red;
    margin-bottom: 10px;
    font-weight: bold;
}
</style>
