<template>
    <div>
        <UIBaseCard customTextAlign="left">
            <div id="introductionText">
                <div id="headline" style="margin: 1% 0%;">
                    <p class="text-4xl">MetaKegg is a tool for everyone...
                    </p>
                </div>
                <p class="text-2xl">
                    Lorem ipsum dolor sit amet, <NuxtLink style="color: blue;" to="https://pubmed.ncbi.nlm.nih.gov/"
                        target="_blank">article</NuxtLink> sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut
                    labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores
                    et
                    ea rebum. Stet clita kasd gubergren, no sea takimata <NuxtLink style="color: blue;"
                        to="https://github.com" target="_blank">documentation</NuxtLink> sanctus est Lorem ipsum dolor
                    sit
                    amet.
                    <NuxtLink style="color: blue;" to="/help">Help</NuxtLink>
                </p>
                <div id="ticketBox" style="text-align: center; margin: 1% 0%">
                    <h1 class="text-3xl" v-if="ticket_id">Your Ticket ID for this session is: {{ ticket_id.id }}
                    </h1>
                </div>
            </div>
        </UIBaseCard>
        <div v-if="healthFetchError || !healthStatus?.healthy">
            <UIBaseCard :narrow-width="true">
                <h1 class="text-3xl font-bold" style="color: red;">There seems to be an error with the server please try
                    again later</h1>
            </UIBaseCard>
        </div>
        <UIBaseCard v-if="healthStatus?.healthy" :narrow-width="true">
            <div class="step-box">
                <h1 class="text-3xl">Step 1: Upload your files</h1>
            </div>
            <div v-if="acceptAGB" style="margin-top: 1%; margin-bottom: 0.5%">
                <UICustomInputField @change="printUploadChange" :label="inputLabel" :checkAGB="acceptAGB" />
            </div>
            <div v-else style="margin-top: 1%; margin-bottom: 0.5%">
                <UButton label="Select your File" variant="outline" @click="uncheckedAGB">
                    <template #trailing>
                        <UIcon name="i-heroicons-cloud-arrow-up" class="w-5 h-5" />
                    </template>
                </UButton>
            </div>
            
            <div style="display: flex; justify-content: center;">
                <UCheckbox v-model="acceptAGB" name="acceptAGB" label="Accept the AGB" />
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
                    valueAttribute="name" style="margin-bottom: 1%"/>
            </div>
            <hr class="custom-hr">
            <div class="step-box">
                <h1 class="text-3xl">Step 3: (Optional) Setting Pipeline Parameters</h1>
            </div>
            <div style="text-align: left">
                <UAccordion v-if="formFields" :items="accordionItems">
                    <template #item="{ item }">
                        <div
                            style="border: solid; border-color: #d3f4e1; border-radius: 1%; padding: 2%; background-color: #f6fdf9;">
                            <UForm :state="formState">
                                <div v-for="(field, key) in formFields" :key="key">
                                    <UFormGroup :label="formatLabel(key)" :required="field.required">
                                        <UInput v-if="['str', 'int', 'float'].includes(field.type)"
                                            v-model="formState[key]" :placeholder="field.default?.toString() || ''"
                                            :type="getInputType(field.type)" @blur="handleBlur(key)" />
                                        <UToggle v-else-if="field.type === 'bool'" v-model="formState[key]"
                                            @blur="handleBlur(key)" />
                                        <UTextarea v-else-if="field.type === 'List'" v-model="formState[key]"
                                            placeholder="Enter items separated by commas" @blur="handleBlur(key)" />
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
            <UButton @click="startPipeline">Start run</UButton>
            <hr class="custom-hr">
            <div class="step-box">
            <h1 class="text-3xl">Step 5: Download your File</h1>
            </div>
            <div v-if="!errorMessage">
                <div v-if="myTestAKAStart">
                    <label for="totalPlaces">totalPlaces</label>
                    <input v-model="totalPlaces" id="totalPlaces" type="text" style="border: solid;">
                    <label for="totalPlaces">currentPlace</label>
                    <input v-model="currentPlace" id="currentPlace" type="text" style="border: solid;">
                    <div style="margin: 2% 0%;">
                    <UProgress :value="progressBar" />
                    <div style="text-align: right; color: #31c363;">
                        <p>Your current place is {{ currentPlace }} out of {{ totalPlaces }}</p>
                    </div>
                </div>
                </div>
                <div v-if="isLoading && pipelineStart">
                    The monkeys are busy in the background please be patient
                    <UProgress animation="carousel" />
                </div>
                <div v-if="!isLoading && downloadStatus">
                    <UButton @click="downloadFile" variant="outline" label="Your File">
                        <template #trailing>
                            <UIcon name="i-heroicons-cloud-arrow-down" class="w-5 h-5" />
                        </template>
                    </UButton>
                </div>
            </div>
            <div v-else>
                <h1 class="text-3xl font-bold" style="color: red; margin: 1% 0%">There seems to be an error: {{ errorMessage }} 
                </h1>
                
                <UAccordion v-if="errorMessageDetail" variant="outline" size="xl" color="red"
                    :items="[{ label: 'Detailed error', content: `${errorMessageDetail}` }]">
                    <template #errorContent>
                        <p style="color: red;">{{ errorMessageDetail }}</p>
                    </template>
                </UAccordion>
            </div>
        </UIBaseCard>
    </div>

</template>

<script setup lang="ts">

const myTestAKAStart = ref(true)
const totalPlaces = ref(30)
const currentPlace = ref(30)

const progressBar = computed(() => {
    return Math.round(100 * (1 - (currentPlace.value / totalPlaces.value)))
})


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

interface Ticket_ID {
    id: string
}

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: config } = await useFetch(`${runtimeConfig.public.baseURL}/config`)
const { data: parameters } = await useFetch(`${runtimeConfig.public.baseURL}/api/params`)
const { data: analysisMethods, error: analysisMethodsError, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)
const { data: ticket_id } = await useFetch<Ticket_ID>(`${runtimeConfig.public.baseURL}/api/pipeline`, {
    method: "POST"
})

const acceptAGB = ref(false)
const pipelineStatus = ref()
const selectedMethod = ref("single_input_genes")
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

        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/upload`, {
            method: 'POST',
            body: formData,
        })
    }
    const status = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/status`)
    pipelineStatus.value = status
}

const errorMessage = ref("")
const errorMessageDetail = ref("")

const isLoading = ref(false)
const pipelineStart = ref(false)
const downloadStatus = ref(false)

async function startPipeline() {
    downloadStatus.value = false
    pipelineStart.value = true
    isLoading.value = true
    errorMessage.value = ""
    errorMessageDetail.value = ""

    if (formDataCheck.value === false) {
        errorMessage.value = "You need to upload a file"
        return
    }

    try {
        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/run/${selectedMethod.value}`, {
            method: "POST"
        })

        while (pipelineStatus.value.state !== 'success' && pipelineStatus.value.state !== 'failed') {
            await new Promise(resolve => setTimeout(resolve, 5000))
            await getStatus()
        }

        if (pipelineStatus.value.state === 'success') {
            downloadStatus.value = true
        }

        if (pipelineStatus.value.error) {
            errorMessage.value = pipelineStatus.value.error
            errorMessageDetail.value = pipelineStatus.value.error_traceback
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
    pipelineStatus.value = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/status`)

    if (pipelineStatus.value.place_in_queue) {
        if (!isMaxPlaceSet.value) {
            maxPlace.value = pipelineStatus.value.place_in_queue
            isMaxPlaceSet.value = true
        }
        pipeLineProgress.value = Math.round(100 * (1 - (pipelineStatus.value.place_in_queue / maxPlace.value)))
    }
}


const formFields = ref(parameters.value);

const formState = ref({});

watchEffect(() => {
    if (formFields.value) {
        Object.entries(formFields.value).forEach(([key, field]: [string, any]) => {
            formState.value[key] = field.default !== undefined ? field.default : null;
        });
    }
});

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

async function handleBlur(fieldName) {
    const missingFields = Object.entries(formFields.value)
        .filter(([key, field]: [string, any]) => field.required && !formState.value[key])
        .map(([key]) => formatLabel(key));

    if (missingFields.length > 0) {
        alert(`"${missingFields.join(', ')}" cannot be empty`);
        formState.value[fieldName] = parameters.value[fieldName].default;
        return;
    }

    await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}?${fieldName}=${formState.value[fieldName]}`, {
        method: "PATCH"
    })

    getStatus()
    console.log(`Field ${fieldName} lost focus value = ${formState.value[fieldName]}`, formState.value);
}


async function downloadFile() {
    try {
        const downloadedFile = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/result`)

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

</script>

<style scoped>
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
    margin: 2% 0%;
}

.custom-hr{
    margin: 2% 0%;
}
</style>
