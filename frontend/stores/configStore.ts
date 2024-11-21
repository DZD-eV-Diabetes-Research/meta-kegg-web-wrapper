import { defineStore } from 'pinia'
import type { Config, InfoLinks } from '~/types'

export const useConfigStore = defineStore('ConfigStore', {
    state: () => {
        return {
            config : {} as Config | null,
            infoLinks: [] as InfoLinks[] | null
        }
    },
    persist: true
})

