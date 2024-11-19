import { defineStore } from 'pinia'

export const usePipelineStore = defineStore('StudyStore', {
    state: () => {
        return {
            errorMessage: "",
            errorStack: "",
            formState: {},
            parameters: "",
            globalParams: [],
            isLoading: false,
            maxPlace: null,
            methodSpecificParams: [],
            pipeLineProgress: 0,
            pipelineStatus: "",
            pipelineStart: false,
            selectedMethod: "single_input_genes",
            ticket_id: "",
            uploadCheck: false,
        }
    },
    persist: true
})
