<template>
    <header
        class="w-full h-[133px] md:h-[10.3vw] max-h-[133px] bg-[#FBFAEE] flex items-center justify-between px-4 md:px-8">
        <div class="metakegg-logo">
            <img src="@/public/img/logos/metakegg.png" alt="MetaKegg-Logo" class="h-12 md:h-20 w-auto">
        </div>
        <div class="flex items-center space-x-4">
            <NuxtLink to="https://dife.de" target="_blank">
                <div class="dife-logo">
                    <img src="@/public/img/logos/dife.png" alt="Dife-Logo" class="h-12 md:h-10 w-auto">
                </div>
            </NuxtLink>
            <NuxtLink to="https://www.dzd-ev.de/" target="_blank">
                <div class="dzd-logo">
                    <img src="@/public/img/logos/dzd.png" alt="DZD-Logo" class="h-12 md:h-14 w-auto">
                </div>
            </NuxtLink>
        </div>
    </header>
</template>