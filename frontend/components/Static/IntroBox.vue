<template>
    <UIBaseCard customTextAlign="left">
        <div id="introductionText" v-if="configStore.config?.entry_text">
            {{ configStore.config?.entry_text }}
        </div>
        <div>
            <h1 style="margin-top: 1%;" class="text-2xl">Linklist</h1>
            <p v-for="link in configStore.infoLinks">
                <NuxtLink style="color: blue" :to="link.link" target="_blank">{{ link.title }}</NuxtLink>
            </p>
        </div>
    </UIBaseCard>
</template>

<script setup lang="ts">
const configStore = useConfigStore()
</script>