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
            The App is loading please be patient
        </UIBaseCard>
    </div>

</template>

<script setup lang="ts">

const runtimeConfig = useRuntimeConfig();

interface HealthStatus {
    healthy: boolean,
    dependencies: []
}

interface Ticket_ID {
    id: string
}

const { data: healthStatus, error: healthFetchError } = await useFetch<HealthStatus>(`${runtimeConfig.public.baseURL}/health`)
const { data: ticket_id } = await useFetch<Ticket_ID>(`${runtimeConfig.public.baseURL}/api/pipeline`, {
    method: "POST"
})

if (ticket_id.value && healthStatus.value?.healthy) {
    console.log(ticket_id.value.id)
    await navigateTo(`/${ticket_id.value.id}`)
}

</script>