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
        </UIBaseCard>
        <div v-if="healthFetchError || !healthStatus?.healthy">
            <UIBaseCard customMaxWidth="50rem">
                <h1 class="text-4xl font-bold" style="color: red;">There seems to be an error with the server please try
                    again later</h1>
            </UIBaseCard>
        </div>
        <UIBaseCard customMaxWidth="75rem" v-if="healthStatus?.healthy">
            <h1 class="text-4xl">Upload your files</h1>
            <br>
            <label for="fileUpload">Select your file or files</label>
            <br>
            <input type="file" name="fileUpload" id="fileUpload" multiple @change="printChange">
            <br>
            <br>
            <div v-if="inputList">
                <p v-for="item in inputList" key="item">{{ item }}</p>
            </div>
            <br>
            <h1 v-if="analysisStatus === 'pending'">Loading</h1>
            <div v-else>
                <label>Select a Method</label>
                <USelect v-model="selectedMethod" :options="analysisMethods" option-attribute="display_name"
                    valueAttribute="internal_id" />
            </div>
            <br>
            <UAccordion color="primary" variant="ghost" size="sm"
                :items="[{ label: 'Advanced Options', content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit' }]" />
            <UButton @click="startPipeline">Start run</UButton>
        </UIBaseCard>
        <UIBaseCard>
            <UContainer v-model="test" :ui="{ icon: { trailing: { pointer: 'pointer-events-auto' } } }" disabled>
                <template #trailing>
                    <UButton icon="i-heroicons-document-duplicate" variant="outline" color="gray"
                        class="rounded-none rounded-r-md -me-2.5"/>
                </template>
            </UContainer>
        </UIBaseCard>
    </div>
    {{ test }}
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

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: analysisMethods, error: analysisMethodsError, status: analysisStatus } = await useFetch<AnalysisMethods[]>(`${runtimeConfig.public.baseURL}/api/analysis`)

const selectedMethod = ref(1)

const inputList = ref<string[]>([])

const selectedFiles = ref<FileList | null>(null)

function printChange(event: Event) {
    const input = event.target as HTMLInputElement

    if (input.files) {
        selectedFiles.value = input.files
        inputList.value = []
        for (const file of input.files) {
            inputList.value.push(file.name)
        }
    }
}

interface Ticket_ID {
    id: string
}

const test = ref()

async function startPipeline() {
    if (!selectedFiles.value || selectedFiles.value.length === 0) {
        console.error('No files selected')
        return
    }

    const ticket_id = await $fetch<Ticket_ID>(`${runtimeConfig.public.baseURL}/api/pipeline`, {
        method: 'POST'
    })

    test.value = ticket_id.id

    const formData = new FormData()
    for (let i = 0; i < selectedFiles.value.length; i++) {
        formData.append('file', selectedFiles.value[i])
    }

    console.log(selectedFiles.value);
    console.log(formData)


    await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${ticket_id.id}/upload`, {
        method: 'POST',
        body: formData,
    })
}


</script>
