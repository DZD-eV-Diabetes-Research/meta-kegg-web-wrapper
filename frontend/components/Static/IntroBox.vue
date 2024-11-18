<template>
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
        </div>
    <p v-for="link in links">
        <li>{{ link.title }} {{ link.link }}</li>
    </p>
        
    </UIBaseCard>
</template>

<script setup lang="ts">
const runtimeConfig = useRuntimeConfig();
const {data: links} = await useFetch(`${runtimeConfig.public.baseURL}/info-links`) 
</script>