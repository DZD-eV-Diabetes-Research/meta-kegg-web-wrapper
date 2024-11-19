import { defineStore } from 'pinia'

export const usePipelineStore = defineStore('StudyStore', {
    state: () => {
        return {
            errorStack: "",
            formState: {},
            parameters: "",
            globalParams: [],
            methodSpecificParams: [],
            pipeLineProgress: 0,
            pipelineStatus: "",
            selectedMethod: "single_input_genes",
            ticket_id: "",
        }
    },
    persist: true
})
