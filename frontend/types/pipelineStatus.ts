export interface PipelineStatus {
    ticket:                        Ticket;
    state:                         string;
    place_in_queue:                number | null;
    error:                         string | null;
    error_traceback:               string | null;
    output_log:                    string | null;
    result_path:                   string | null;
    pipeline_params:               PipelineParams;
    pipeline_analyses_method:      PipelineAnalysesMethod;
    pipeline_input_file_names:     string[] | null;
    pipeline_output_zip_file_name: string | null;
    created_at_utc:                Date;
    started_at_utc:                string | null;
    finished_at_utc:               string | null;
}

export interface PipelineAnalysesMethod {
    name:         string;
    display_name: string;
    internal_id:  number;
    desc:         string | null;
}

export interface PipelineParams {
    global_params:          GlobalParams;
    method_specific_params: MethodSpecificParams;
}

export interface GlobalParams {
    input_label:      string[];
    sheet_name_paths: string;
    sheet_name_genes: string;
    genes_column:     string;
    log2fc_column:    string;
    compounds_list:   string[] | null;
    save_to_eps:      boolean;
}

export interface MethodSpecificParams {
    [key: string]: string | number | boolean | string[] | null;
}

export interface Ticket {
    id: string;
}