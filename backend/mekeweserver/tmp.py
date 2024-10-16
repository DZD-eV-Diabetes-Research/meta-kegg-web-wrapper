    input_file_path: str = Field( description='Path to the input file (Excel format) or list of input files. Can be a David analysis output, or RNAseq')
    sheet_name_paths: str = Field( default='pathways', description='Sheet name containing the pathway information (see docs). Has to apply to all input files in case of multiple.')
    sheet_name_genes: str = Field( default='gene_metrics', description='Sheet name for gene information (see docs). Has to apply to all input files in case of multiple.')
    genes_column: str = Field( default='gene_symbol', description='Column name for gene symbols in the sheet_name_genes')
    log2fc_column: str = Field( default='logFC', description='Column name for log2fc values in the sheet_name_genes')
    analysis_type: str = Field( type=int, default=None, choices=[1, 2, 3, 4, 5, 6, 7, 8, 9] ,description='Analysis type (1-9)')
    count_threshold: str = Field( type=int, default=2, description='Minimum number of genes per pathway, for pathway to be drawn. Default value : 2')
    pathway_pvalue: str = Field( type=float, default=None, description='Raw p-value threshold for the pathways')
    input_label: str = Field( default=None, description='Input label or list of labels for multiple inputs')
    folder_extension: str = Field( default=None, description='Folder extension to be appended to the default naming scheme. If None and default folder exists, will overwrite folder')
    methylation_path: str = Field( default=None, description='Path to methylation data (Excel , CSV or TSV format)')
    methylation_pvalue: str = Field( default=None, description='Column name for methylation p-value')
    methylation_genes: str = Field( default=None, description='Column name for methylation gene symbols')
    methylation_pvalue_thresh: str = Field( type=float, default=0.05, description='P-value threshold for the methylation values')
    methylation_probe_column: str = Field( default=None, description='Column name for the methylation probes.')
    probes_to_cgs: str = Field( default=False, description='If True, will correct the probes to positions, delete duplicated positions and keep the first CG.')
    miRNA_path: str = Field( default=None, description='Path to miRNA data (Excel , CSV or TSV format)')
    miRNA_pvalue: str = Field( default=None, description='Column name for miRNA p-value')
    miRNA_genes: str = Field( default=None, description='Column name for miRNA gene symbols')
    miRNA_pvalue_thresh: str = Field( type=float ,default=0.05, description='P-value threshold for the miRNA values')
    miRNA_ID_column: str = Field( default=None, description='Column name for the miRNA IDs.') 
    benjamini_threshold: str = Field( type=float, default=None, description='Benjamini Hochberg p-value threshold for the pathway')
    save_to_eps: str = Field( default=False, description='True/False statement to save the maps and colorscales or legends as seperate .eps files in addition to the .pdf exports')
    output_folder_name: str = Field( default=None, description='Name of output folder. Will overpower default scheme. Combines with extension')
    