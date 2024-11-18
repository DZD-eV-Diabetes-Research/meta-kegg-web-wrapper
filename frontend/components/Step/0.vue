<template>
    <div class="step-box">
        <h1 class="text-3xl mb-6">Step 0: Copy Your MetaKegg-URL</h1>
    </div>
    <UButton :label="url.toString()" color="gray" @click="copyToClipboard">
        <template #trailing>
            <UIcon :name="icon" class="w-5 h-5" />
        </template>
    </UButton>
    <div v-show="showCopyMessage" class="notification-box">
        <p class="mb-2">{{ copyMessage }}</p>
        <div class="w-full">
            <UProgress :value="copyProgress" />
        </div>
    </div>
</template>

<script setup lang="ts">
const url = useRequestURL()

const { copy } = useClipboard();


const icon = ref("i-heroicons-clipboard-document");
const copyMessage = ref("");
const copyProgress = ref(0);
const showCopyMessage = ref(false);

const copyToClipboard = async () => {
    const success = await copy(url.toString());
    if (success) {
        icon.value = "i-heroicons-clipboard-document-check";
        copyMessage.value = "URL successfully copied to clipboard";
        copyProgress.value = 100;
        showCopyMessage.value = true;

        const startTime = performance.now();
        const duration = 2500;

        const animate = (currentTime) => {
            const elapsedTime = currentTime - startTime;
            const progress = Math.max(0, 100 - (elapsedTime / duration) * 100);

            copyProgress.value = progress;

            if (elapsedTime < duration) {
                requestAnimationFrame(animate);
            } else {
                setTimeout(() => {
                    showCopyMessage.value = false;
                }, 500);

                setTimeout(() => {
                    icon.value = "i-heroicons-clipboard-document";
                    copyMessage.value = "";
                    copyProgress.value = 0;
                }, 1000);
            }
        };

        requestAnimationFrame(animate);
    } else {
        console.error('Failed to copy URL');
    }
};

</script>

<style scoped>
.copy-message-container {
    opacity: 1;
    transition: opacity 0.5s ease-out;
}

.copy-message-container[style*="display: none"] {
    opacity: 0;
}


.notification-box {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    width: 300px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    opacity: 1;
    transition: opacity 0.5s ease-out;
    z-index: 1000;
}

.notification-box[style*="display: none"] {
    opacity: 0;
}
</style>