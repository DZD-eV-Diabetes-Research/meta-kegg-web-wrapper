<template>
    <div class="step-box" style="">
        <h1 class="text-3xl">Step 5: Download your File</h1>
    </div>
    <div v-if="!pipelineStore?.pipelineStatus?.error">
        <div v-if="pipelineStore.pipelineStatus?.state === 'queued'">
            <div style="margin: 2% 0%;">
                <p>You are placed in a queue, please be patient.
                </p>
                <UProgress :value="pipelineStore.pipeLineProgress" />
                <div style="text-align: right; color: #31c363;">
                    <p>Your current place is {{ pipelineStore.pipelineStatus?.place_in_queue! + 1 }} out of {{
                        pipelineStore.maxPlace }}</p>
                </div>
            </div>
        </div>
        <div
            v-else-if="pipelineStore.isLoading && pipelineStore.pipelineStart && pipelineStore.pipelineStatus?.state === 'running'">
            <div style="margin: 2% 0%;">
                <p>The monkeys are busy in the background please be patient</p>
                <UProgress animation="carousel" />
            </div>
        </div>
        <div v-else-if="!pipelineStore.isLoading && pipelineStore.pipelineStatus?.state === 'success'">
            <UButton @click="downloadFile" variant="outline" label="Your File">
                <template #trailing>
                    <UIcon name="i-heroicons-cloud-arrow-down" class="w-5 h-5" />
                </template>
            </UButton>
        </div>
    </div>
    <div v-else>
        <h1 class="text-3xl font-bold" style="color: red; margin: 1% 0%">There seems to be an error: {{
            pipelineStore.errorMessage }}
        </h1>
        <UAccordion v-if="pipelineStore.errorStack" variant="outline" size="xl" color="red"
            :items="[{ label: 'Detailed error', content: `${pipelineStore.errorStack}` }]">
            <template #item="{ item }">
                <div style="text-align: left;">
                    <p style="color: red;" v-html="item.content" />
                    <br>
                    <div
                        style="display: flex; justify-content: center; align-items: center; height: 100%; width: 100%;">
                        <div style="border: solid 1px;" class="email-support-container">
                            <a class="text-3xl" style="padding: 15px;"
                                :href="`mailto:${config?.bug_report_email}?subject=Error Metakegg: ${encodeURIComponent(pipelineStore.errorMessage)} &body=During the run of the following URL: %0D%0A %0D%0A ${url.toString()}   %0D%0A %0D%0A The page returned the following %0D%0A%0D%0A Errorstack:  %0D%0A%0D%0A  ${encodeURIComponent(pipelineStore?.pipelineStatus?.error_traceback)}`">
                                Send a mail to our support
                                <UIcon name="i-heroicons-paper-airplane" class="w-5 h-5" />
                            </a>
                        </div>
                    </div>
                </div>
            </template>
        </UAccordion>
    </div>
</template>

<script setup lang="ts">
import type { Config } from '~/types';

const url = useRequestURL()
const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();
const { data: config } = await useFetch<Config>(`${runtimeConfig.public.baseURL}/config`)

async function downloadFile() {
    try {
        const downloadedFile = await $fetch(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id}/result`)

        const blobUrl = URL.createObjectURL(downloadedFile);

        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = pipelineStore?.pipelineStatus?.pipeline_output_zip_file_name;

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
.email-support-container:hover {
    background-color: #f0f0f0;
}
</style>