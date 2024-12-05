<template>
    <div>
        <StaticIntroBox />
        <div v-if="healthFetchError || !healthStatus?.healthy">
            <UIBaseCard :narrow-width="true">
                <h1 class="text-3xl font-bold" style="color: red;">There seems to be an error with the server please try
                    again later</h1>
            </UIBaseCard>
        </div>
        <UIBaseCard v-if="healthStatus?.healthy" :narrow-width="true">
            The App is loading please be patient
        </UIBaseCard>
        <UIBaseCard v-if="configError || linkError || ticketError" :narrow-width="true">
            <h1 class="text-3xl font-bold" style="color: red;">There seems to be an error {{ configError?.message ?? linkError?.message ?? ticketError?.message}}</h1>
        </UIBaseCard>
    </div>
</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig();
const configStore = useConfigStore()

interface HealthStatus {
    healthy: boolean,
    dependencies: []
}

interface Ticket_ID {
    id: string
}

const { data: config, error: configError } = await useFetch<Config>(`${runtimeConfig.public.baseURL}/config`)
configStore.config = config.value

const { data: infoLinks, error: linkError } = await useFetch<InfoLinks[]>(`${runtimeConfig.public.baseURL}/info-links`)
configStore.infoLinks = infoLinks.value

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: ticket_id, error: ticketError } = await useFetch<Ticket_ID>(`${runtimeConfig.public.baseURL}/api/pipeline`, {
    method: "POST"
    
})

if (ticket_id.value && healthStatus.value?.healthy) {
    await navigateTo(`/${ticket_id.value.id}`)
}

</script>