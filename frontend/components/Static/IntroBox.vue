<template>
    <UIBaseCard customTextAlign="left">
        <div id="introductionText">
            {{ config.entry_text }}
        </div>
        <div>
            <h1 style="margin-top: 1%;" class="text-2xl">Linklist</h1>
            <p v-for="link in links">
                <NuxtLink style="color: blue":to="link.link" :target="_blank">{{ link.title }}</NuxtLink>
            </p>
        </div>
    </UIBaseCard>
</template>

<script setup lang="ts">
const runtimeConfig = useRuntimeConfig();
const { data: config } = await useFetch(`${runtimeConfig.public.baseURL}/config`)
const { data: links } = await useFetch(`${runtimeConfig.public.baseURL}/info-links`) 
</script>