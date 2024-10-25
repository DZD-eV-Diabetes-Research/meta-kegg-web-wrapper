<template>
    <footer class="w-full h-[133px] md:h-[10.3vw] max-h-[133px] bg-[#FBFAEE] flex items-center px-8">
        <div class="flex flex-col items-start">
            <NuxtLink to="https://www.helmholtz-munich.de/" target="_blank" class="mb-2">
                <img src="@/public/img/logos/helmholtz.png" alt="Helmholtz Logo" class="h-8 md:h-12 w-auto">
            </NuxtLink>
            <NuxtLink to="https://github.com/dife-bioinformatics/metaKEGG" target="_blank"
                class="text-sm text-gray-600 hover:text-gray-800">
                Documentation
            </NuxtLink>
        </div>
    </footer>
</template>