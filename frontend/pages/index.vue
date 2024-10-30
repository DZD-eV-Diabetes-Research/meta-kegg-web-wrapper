<template>
    <div>
        <UIBaseCard customTextAlign="left">
            <p class="text-4xl">MetaKegg is a tool for everyone...
            </p>
            <br>
            <p class="text-2xl">
                Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut
                labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et
                ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.
            </p>
            <br>
            <div style="text-align: center;">
                <h1 class="text-3xl" v-if="ticket_id">Your Ticket ID for this session is:<br> {{ ticket_id.id }}</h1>
            </div>
        </UIBaseCard>
        <div v-if="healthFetchError || !healthStatus?.healthy">
            <UIBaseCard customMaxWidth="50rem">
                <h1 class="text-3xl font-bold" style="color: red;">There seems to be an error with the server please try
                    again later</h1>
            </UIBaseCard>
        </div>
        <UIBaseCard customMaxWidth="75rem" v-if="healthStatus?.healthy">
            <h1 class="text-3xl">Step 1: Upload your files</h1>
            <br>
            <label v-if="!pipelineStatus?.pipeline_input_file_names" for="fileUpload">Select your file</label>
            <label v-else for="fileUpload">Add an additional File</label>
            <br>
            <br>
            <input class="metaKegg-input" type="file" name="fileUpload" id="fileUpload" @change="printUploadChange">
            <br>
            <br>
            <div v-if="pipelineStatus?.pipeline_input_file_names.length > 0">
                <p> Uploaded Files </p>
                <p v-for="item in pipelineStatus?.pipeline_input_file_names" key="item">{{ item }}</p>
            </div>
            <br>
            <hr>
            <br>
            <h1 class="text-3xl">Step 2: Select an Analysis Method</h1>
            <br>
            <h1 v-if="analysisStatus === 'pending'">Loading</h1>
            <div v-else class="select-container">
                <USelect v-model="selectedMethod" :options="analysisMethods" option-attribute="display_name"
                    valueAttribute="name" />
            </div>
            <br>
            <hr>
            <br>
            <h1 class="text-3xl">Step 3: (Optional) Setting Pipeline Parameters</h1>
            <br>
            <UAccordion color="primary" variant="ghost" size="xl"
                :items="[{ label: 'Pipeline Parameter Setting', content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit' }]"
                :ui="{ wrapper: 'flex flex-col w-full', container: 'flex justify-center' }" />

            <br>
            <hr>
            <br>
            <h1 class="text-3xl">Step 4: Start the Pipeline</h1>
            <br>
            <UButton @click="startPipeline">Start run</UButton>
            <br>
            <br>
            <hr>
            <br>
            <h1 class="text-3xl">Step 5: Download your File</h1>
            <br>
            <div v-if="isLoading && pipelineStart">
                The monkeys are busy in the background please be patient
                <UProgress animation="carousel" />
            </div>
            <div v-if="!isLoading && downloadStatus">
                <UButton @click="downloadFile">Your File</UButton>
            </div>
        </UIBaseCard>
    </div>
</template>

<script setup lang="ts">

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
const { data: analysisMethods, error: analysisMethodsError, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)
const { data: ticket_id } = await useFetch<Ticket_ID>(`${runtimeConfig.public.baseURL}/api/pipeline`, {
    method: "POST"
})

const pipelineStatus = ref()

const selectedMethod = ref("single_input_genes")

async function printUploadChange(event: Event) {
    const input = event.target as HTMLInputElement

    if (input.files && input.files.length > 0) {
        const formData = new FormData()
        formData.append('file', input.files[0])

        await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/upload`, {
            method: 'POST',
            body: formData,
        })
    }
    const status = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/status`)
    pipelineStatus.value = status
}

const myResponse = ref()

const isLoading = ref(false)
const pipelineStart = ref(false)
const downloadStatus = ref(false)

async function startPipeline() {
    downloadStatus.value = false
    pipelineStart.value = true
    isLoading.value = true

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
    } catch (error) {
        console.error('Error in pipeline:', error)
    } finally {
        isLoading.value = false
        pipelineStart.value = false
    }
}
async function getStatus() {
    pipelineStatus.value = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.value?.id}/status`)
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

.metaKegg-input {
    font-family: 'Poppins';
    padding: 0;
    margin: 0;
}
</style>
