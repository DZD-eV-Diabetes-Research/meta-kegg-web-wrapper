export function useCustomCopyToClipboard() {
    const icon = ref("i-heroicons-clipboard-document");
    const copyMessage = ref("");
    const copyProgress = ref(0);
    const showCopyMessage = ref(false);

    const copyToClipboard = async (textToCopy: string) => {
        const copy = async (text: string) => {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (err) {
                console.error('Failed to copy text: ', err);
                return false;
            }
        };

        const success = await copy(textToCopy);
        if (success) {
            icon.value = "i-heroicons-clipboard-document-check";
            copyMessage.value = "URL successfully copied to clipboard";
            copyProgress.value = 100;
            showCopyMessage.value = true;

            const startTime = performance.now();
            const duration = 2500;

            const animate = (currentTime: number) => {
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

    return {
        icon,
        copyMessage,
        copyProgress,
        showCopyMessage,
        copyToClipboard
    };
}