from typing import List, Dict
import json
from pathlib import Path, PurePath

import requests
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    find_first_dict_in_list,
)


def test_single_input_gene_pipeline_run():
    res = req(
        "/api/pipeline",
        method="post",
        q={
            "sheet_name_paths": "pathways",
            "sheet_name_genes": "gene_metrics",
            "input_label": "input",
            "save_to_eps": "True",
            "count_threshold": 3,
            "benjamini_threshold": None,
        },
    )
    dict_must_contain(
        res,
        required_keys=["id"],
        exception_dict_identifier="POST-'/api/pipeline'-response",
    )
    pipeline_ticket_id: str = res["id"]
    res = req(
        f"/api/pipeline/{pipeline_ticket_id}",
        method="patch",
        q={"count_threshold": 2},
    )
    dict_must_contain(
        res,
        required_keys=["pipeline_params"],
        exception_dict_identifier="PATCH-'/api/pipeline/{pipeline_ticket_id}'-response",
    )
    dict_must_contain(
        res["pipeline_params"],
        required_keys_and_val={"count_threshold": 2},
        exception_dict_identifier="PATCH-'/api/pipeline/{pipeline_ticket_id}'-response",
    )
    test_upload_file_single_input_gene_path = Path(
        PurePath(Path(__file__).parent, "provisioning_data/single_input_genes.xlsx")
    )
    with open(test_upload_file_single_input_gene_path, "rb") as input_file:

        res = req(
            f"/api/pipeline/{pipeline_ticket_id}/upload",
            method="post",
            form_file=("single_input_genes.xlsx", input_file),
        )
    dict_must_contain(
        res,
        required_keys_and_val={
            "pipeline_input_file_names": ["single_input_genes.xlsx"]
        },
        exception_dict_identifier="POST-'/api/pipeline/{pipeline_ticket_id}/upload'-response",
    )
    res = req(
        f"/api/pipeline/{pipeline_ticket_id}/status",
    )
    dict_must_contain(
        res,
        required_keys_and_val={"state": "initialized"},
        exception_dict_identifier="GET-'/api/pipeline/{pipeline_ticket_id}/status'-response",
    )
    res = req(
        f"/api/pipeline/{pipeline_ticket_id}/run/single_input_genes", method="post"
    )
    dict_must_contain(
        res,
        required_keys_and_val={"state": "queued"},
        exception_dict_identifier="GET-'/api/pipeline/{pipeline_ticket_id}/status'-response",
    )


def run_all_tests_pipeline_run():
    test_single_input_gene_pipeline_run()
