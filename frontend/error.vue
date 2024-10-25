<template>
    <NuxtLayout>
        <Layout>
            <UIBaseCard>
                <p class="text-4xl" style="text-align: center;">There is nothing to see here please go back</p>
                <div style="display: flex; justify-content: center; margin-top: 1rem;">
                    <ClientOnly>
                        <video width="640" height="480" autoplay loop>
                            <source src="@/public/video/naked-gun-please-disperse.mp4" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </ClientOnly>
                </div>
            </UIBaseCard>
            <div style="text-align: center; margin-bottom: 2rem">
                <UButton color="white" variant="solid" size="xl">
                    <NuxtLink to="/">Return</NuxtLink>
                </UButton>
            </div>
        </Layout>
    </NuxtLayout>
</template>

<script>
useHead({
    title: 'MetaKegg',
    meta: [
        { name: 'description', content: 'Dife-DZD Webapp to do MetaKegg stuff' }
    ],
})
</script>