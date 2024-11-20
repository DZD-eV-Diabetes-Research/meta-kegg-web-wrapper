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
                <h3 class="text-4xl">The current expiration time is: {{ config?.pipeline_ticket_expire_time_sec ?? 86400 / 3600 }}
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
            <Step4/>
            <hr class="custom-hr">
            <Step5/>
        </UIBaseCard>
    </div>
</template>

<script setup lang="ts">
import type { HealthStatus, PipelineParams, PipelineStatus, Config } from '~/types';

const pipelineStore = usePipelineStore()
const runtimeConfig = useRuntimeConfig();

const route = useRoute()
pipelineStore.ticket_id  = route.params.id as string

const { data: pipelineStatus, error: statusError } = await useFetch<PipelineStatus>(`${runtimeConfig.public.baseURL}/api/pipeline/${pipelineStore.ticket_id }/status`)
pipelineStore.pipelineStatus = pipelineStatus.value

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: config } = await useFetch<Config>(`${runtimeConfig.public.baseURL}/config`)

const { data: parameters } = await useFetch<PipelineParams>(`${runtimeConfig.public.baseURL}/api/${pipelineStore.selectedMethod}/params`)
pipelineStore.parameters = parameters.value

function newID() {
    navigateTo("/")
}
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
</style>
