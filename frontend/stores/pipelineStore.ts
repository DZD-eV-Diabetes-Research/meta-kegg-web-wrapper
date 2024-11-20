import { defineStore } from 'pinia'
import type { PipelineStatus, PipelineParams, GlobalParams, MethodSpecificParams, FormState } from '~/types'

export const usePipelineStore = defineStore('PipelineStore', {
    state: () => {
        return {
            errorMessage: "",
            errorStack: "",
            formState: {} as FormState,
            parameters: null as PipelineParams | null,
            globalParams: null as GlobalParams | null,
            isLoading: false,
            maxPlace: null as number | null,
            methodSpecificParams: null as MethodSpecificParams | null,
            pipeLineProgress: 0,
            pipelineStatus: null as PipelineStatus | null,
            pipelineStart: false,
            requiredFieldsError: "",
            selectedMethod: "single_input_genes",
            ticket_id: "",
            uploadCheck: false,
            uploadErrorMessage: "",
        }
    },
    persist: true
})

