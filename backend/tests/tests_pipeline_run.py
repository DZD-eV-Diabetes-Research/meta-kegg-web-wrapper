from typing import List, Dict
import os
import re
import json
import uuid
from pathlib import Path, PurePath
import time
import requests
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    find_first_dict_in_list,
    get_dot_env_file_variable,
)


def test_metadata_endpoints():
    res = req(
        "/api/analysis",
        method="get",
    )
    assert isinstance(res, list)
    assert len(res) > 3
    for method in res:
        dict_must_contain(
            method,
            required_keys=["name", "display_name", "desc"],
            exception_dict_identifier=f"method info for '{method}'",
        )
        res_params = req(
            f"/api/{method['name']}/params",
            method="get",
        )
        dict_must_contain(
            res_params,
            required_keys=["global_params", "method_specific_params"],
            exception_dict_identifier=f"params for method '{method['name']}'",
        )
        assert (
            len(res_params["global_params"]) > 3
        ), f"Oh no 'global_params' is to short: {res_params['global_params']}"
    # config
    res = req(
        "/config",
        method="get",
    )
    dict_must_contain(
        res,
        required_keys_and_val={
            "contact_email": "test@blop.de",
            "bug_report_email": "test@blop.de",
        },
        required_keys=["terms_and_conditions", "pipeline_ticket_expire_time_sec"],
        exception_dict_identifier=f"client config",
    )
    # info-links
    res = req(
        "/info-links",
        method="get",
    )
    dict_must_contain(
        res[0],
        required_keys_and_val={"title": "link1", "link": "https://doi.org/12345"},
        exception_dict_identifier=f"link list",
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
    timeout_end = time.time() + 120
    pipeline_running = True
    while pipeline_running and timeout_end > time.time():
        res = req(
            f"/api/pipeline/{pipeline_ticket_id}/status",
        )
        print("res", res["state"])
        if res["state"] == "failed":
            print("")
            print(
                f"ERROR: Pipeline-run with id '{pipeline_ticket_id}'. Traceback:\n{res['error_traceback']}"
            )
            print("")
            raise ValueError("Pipeline failed. See traceback above")
        elif res["state"] == "success":
            pipeline_running = False
        time.sleep(1)
    # download result file
    res: requests.Response = req(
        f"/api/pipeline/{pipeline_ticket_id}/result", return_response_obj=True
    )
    d = res.headers["content-disposition"]
    downloaded_file_name = re.findall("filename=(.+)", d)[0].strip('"')

    test_data_base_path = Path(
        PurePath(
            get_dot_env_file_variable(
                "backend/tests/.env", "PIPELINE_RUNS_CACHE_DIR", missing_ok=False
            ),
            uuid.UUID(pipeline_ticket_id).hex,
        )
    )
    source_file = Path(
        PurePath(
            test_data_base_path,
            "output",
            downloaded_file_name,
        )
    )
    target_file = Path(
        PurePath(
            test_data_base_path,
            "result_download.zip",
        )
    )
    with open(target_file, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)
    assert source_file.stat().st_size == target_file.stat().st_size


def run_all_tests_pipeline_run():
    test_metadata_endpoints()
    test_single_input_gene_pipeline_run()
