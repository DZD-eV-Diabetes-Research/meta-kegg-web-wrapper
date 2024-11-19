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
            <Step0/>
            <hr class="custom-hr">
            <Step1/>
            <hr class="custom-hr">
            <Step2/>
            <hr class="custom-hr">
            <Step3/>
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
                <div v-if="pipelineStore.pipelineStatus?.state === 'queued'">
                    <div style="margin: 2% 0%;">
                        <p>You are placed in a queue, please be patient.
                        </p>
                        <UProgress :value="pipelineStore.pipeLineProgress" />
                        <div style="text-align: right; color: #31c363;">
                            <p>Your current place is {{ pipelineStore.pipelineStatus?.place_in_queue + 1 }} out of {{ maxPlace }}</p>
                        </div>
                    </div>
                </div>
                <div v-else-if="isLoading && pipelineStart && pipelineStore.pipelineStatus?.state === 'running'">
                    <p style="margin-bottom: 0.5%;">The monkeys are busy in the background please be patient</p>
                    <UProgress animation="carousel" />
                </div>
                <div v-else-if="!isLoading && pipelineStore.pipelineStatus?.state === 'success'">
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
                                <div style="border: solid 1px;" class="email-support-container">
                                    <a class="text-3xl" style="padding: 15px;"
                                        :href="`mailto:${config.bug_report_email}?subject=Error Metakegg&body=During the run of the following URL: %0D%0A %0D%0A ${url.toString()}   %0D%0A %0D%0A The page returned the following %0D%0A%0D%0A Errorstack:  %0D%0A%0D%0A  ${encodeURIComponent(errorStack)}`">
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
    {{ pipelineStatus }}
    <br>
    <br>
    {{ pipelineStore.parameters  }}
    <br>
    <br>
    {{ pipelineStore.pipelineStatus  }}
</template>

<script setup lang="ts">

const pipelineStore = usePipelineStore()
const url = useRequestURL()
const route = useRoute()
pipelineStore.ticket_id  = route.params.id as string


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


const selectedMethod = ref("single_input_genes")

const { data: pipelineStatus, error: statusError } = await useFetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/status`)
pipelineStore.pipelineStatus = pipelineStatus

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: config } = await useFetch(`${runtimeConfig.public.baseURL}/config`)
const { data: parameters } = await useFetch(`${runtimeConfig.public.baseURL}/api/${selectedMethod.value}/params`)
pipelineStore.parameters = parameters

const errorStack = ref("")
const { data: analysisMethods, error: analysisMethodsError, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)

const formDataCheck = ref(false)

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

const maxPlace = ref()
const isMaxPlaceSet = ref(false)

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
        pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/run/${selectedMethod.value}`, {
            method: "POST"
        })

        if (pipelineStore.pipelineStatus.place_in_queue) {

            if (!isMaxPlaceSet.value) {
                maxPlace.value = pipelineStore.pipelineStatus.place_in_queue
                isMaxPlaceSet.value = true


            }
            pipelineStore.pipeLineProgress = Math.round(100 * ((pipelineStore.pipelineStatus.place_in_queue / maxPlace.value)))

        }

        await getStatus()

        while (pipelineStore.pipelineStatus.state !== 'success' && pipelineStore.pipelineStatus.state !== 'failed') {
            await new Promise(resolve => setTimeout(resolve, 5000))
            await getStatus()
        }

        if (pipelineStore.pipelineStatus.state === 'success') {
            downloadStatus.value = true
        }

        if (pipelineStore.pipelineStatus.error) {
            errorMessage.value = pipelineStore.pipelineStatus.error
            errorMessageDetail.value = pipelineStore.pipelineStatus.error_traceback.replace(/\n/g, `<br>`)
        }


    } catch (error) {
        console.error('Error in pipeline:', error)
    } finally {
        isLoading.value = false
        pipelineStart.value = false
    }
}

async function getStatus() {
    pipelineStore.pipelineStatus = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/status`)

    if (pipelineStore.pipelineStatus.place_in_queue) {
        pipelineStore.pipeLineProgress = Math.round(100 * ((pipelineStore.pipelineStatus.place_in_queue / maxPlace.value)))
    }
    errorStack.value = pipelineStore.pipelineStatus.error_traceback
}


function formatLabel(key: string): string {
    return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

const globalParams = ref([])
const methodSpecificParams = ref([]);

const formState = ref({});

onMounted(() => {
    if (pipelineStore.parameters) {
        globalParams.value = pipelineStore.parameters.global_params || [];
        methodSpecificParams.value = pipelineStore.parameters.method_specific_params || [];
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

    if (pipelineStore.pipelineStatus && pipelineStore.pipelineStatus.pipeline_params) {
        Object.entries(pipelineStore.pipelineStatus.pipeline_params).forEach(([key, value]) => {
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
watch(() => pipelineStore.pipelineStatus?.pipeline_params, (newParams) => {
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
        const url = `${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }`;
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
        const downloadedFile = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/result`)

        const blobUrl = URL.createObjectURL(downloadedFile);

        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = pipelineStore.pipelineStatus.pipeline_output_zip_file_name + '.zip';

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

watch(() => pipelineStore.pipelineStatus?.pipeline_input_file_names, (newValue) => {
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

.email-support-container:hover {
    background-color: #f0f0f0;
}
</style>
