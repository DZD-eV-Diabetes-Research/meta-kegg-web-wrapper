<template>
    <NuxtLayout>
        <Layout>
            <UIBaseCard>
                <p class="text-4xl" style="text-align: center;">Sorry we couldn't find the page you were looking for</p>
                <div style="display: flex; justify-content: center; margin-top: 1rem;">
                        <video width="640" height="480" autoplay loop muted playsinline>
                            <source src="@/public/video/naked-gun-please-disperse.mp4" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                </div>
            </UIBaseCard>
            <div style="text-align: center; margin-bottom: 2rem; display: flex; justify-content: center">
                <div style="margin-left: 2%;">
                    <UButton color="white" variant="solid" size="xl">
                        <NuxtLink to="/">Create new URL</NuxtLink>
                    </UButton>
                </div>
            </div>
        </Layout>
    </NuxtLayout>
</template>

<script setup lang="ts">
useHead({
    title: 'MetaKegg',
    meta: [
        { name: 'description', content: 'Dife-DZD Webapp to do MetaKegg stuff' }
    ],
})
</script>