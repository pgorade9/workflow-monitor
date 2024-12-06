import requests


def get_workflow_payload(dag, data_partition_id, adme_dns_host, token, sub_key, file_id, file_name):
    print("Creating Workflow Payload ***************************")
    print(f"{dag=}")
    workflow_payload = {
        "executionContext": {
            "dataPartitionId": f"{data_partition_id}",
            "id": f"{file_id}"
        }
    }

    if dag == "Osdu_ingest":
        print("Dag is Osdu_Ingest ***************************")
        workflow_payload = {
            "executionContext": {
                "Payload": {
                    "AppKey": "test-app",
                    "data-partition-id": f"{data_partition_id}"
                },
                "manifest": {
                    "kind": "osdu:wks:Manifest:1.0.0",
                    "ReferenceData": [],
                    "MasterData": [],
                    "Data": {
                        "WorkProduct": {
                            "id": f"{data_partition_id}:work-product--WorkProduct:0d409294-effd-4103-bb89-b7fb7471c444:2abcd",
                            "kind": f"{data_partition_id}:wks:work-product--WorkProduct:1.0.0",
                            "acl": {
                                "owners": [
                                    f"data.default.owners@{data_partition_id}.enterprisedata.cloud.slb-ds.com"
                                ],
                                "viewers": [
                                    f"data.default.viewers@{data_partition_id}.enterprisedata.cloud.slb-ds.com"
                                ]
                            },
                            "legal": {
                                "legaltags": [
                                    f"{data_partition_id}-default-legal"
                                ],
                                "otherRelevantDataCountries": [
                                    "US"
                                ]
                            },
                            "data": {
                                "Name": f"{file_name}",
                                "Description": "Document",
                                "Components": [
                                    f"{file_id}:"
                                ]
                            }
                        },
                        "WorkProductComponents": [
                            {
                                "id": f"{file_id}",
                                "kind": f"{data_partition_id}:wks:work-product-component--WellboreMarkerSet:1.0.0",
                                "acl": {
                                "owners": [
                                    f"data.default.owners@{data_partition_id}.enterprisedata.cloud.slb-ds.com"
                                ],
                                "viewers": [
                                    f"data.default.viewers@{data_partition_id}.enterprisedata.cloud.slb-ds.com"
                                ]
                            },
                                "legal": {
                                "legaltags": [
                                    f"{data_partition_id}-default-legal"
                                ],
                                "otherRelevantDataCountries": [
                                    "US"
                                ]
                            },
                                "data": {
                                    "Name": f"{file_name}",
                                    "Description": "Wellbore Marker",
                                    "Datasets": [
                                        "default-qa-sis-internal-hq:dataset--File.Generic:5b718938-3635-4b6b-9d40-447ad5a816db:"
                                    ],
                                    "Markers": [
                                        {
                                            "MarkerName": "North Sea Supergroup",
                                            "MarkerMeasuredDepth": 0.0
                                        },
                                        {
                                            "MarkerName": "Ommelanden Formation",
                                            "MarkerMeasuredDepth": 1555.0
                                        },
                                        {
                                            "MarkerName": "Texel Marlstone Member",
                                            "MarkerMeasuredDepth": 2512.5
                                        },
                                        {
                                            "MarkerName": "Upper Holland Marl Member",
                                            "MarkerMeasuredDepth": 2606.0
                                        },
                                        {
                                            "MarkerName": "Middle Holland Claystone Member",
                                            "MarkerMeasuredDepth": 2723.0
                                        },
                                        {
                                            "MarkerName": "Vlieland Claystone Formation",
                                            "MarkerMeasuredDepth": 2758.0
                                        },
                                        {
                                            "MarkerName": "Lower Volpriehausen Sandstone Member",
                                            "MarkerMeasuredDepth": 2977.5
                                        },
                                        {
                                            "MarkerName": "Rogenstein Member",
                                            "MarkerMeasuredDepth": 3018.0
                                        },
                                        {
                                            "MarkerName": "FAULT",
                                            "MarkerMeasuredDepth": 3043.0
                                        },
                                        {
                                            "MarkerName": "Upper Zechstein salt",
                                            "MarkerMeasuredDepth": 3043.0
                                        },
                                        {
                                            "MarkerName": "FAULT",
                                            "MarkerMeasuredDepth": 3544.0
                                        },
                                        {
                                            "MarkerName": "Z3 Carbonate Member",
                                            "MarkerMeasuredDepth": 3544.0
                                        },
                                        {
                                            "MarkerName": "Z3 Main Anhydrite Member",
                                            "MarkerMeasuredDepth": 3587.0
                                        },
                                        {
                                            "MarkerName": "FAULT",
                                            "MarkerMeasuredDepth": 3622.0
                                        },
                                        {
                                            "MarkerName": "Z3 Salt Member",
                                            "MarkerMeasuredDepth": 3622.0
                                        },
                                        {
                                            "MarkerName": "Z3 Main Anhydrite Member",
                                            "MarkerMeasuredDepth": 3666.5
                                        },
                                        {
                                            "MarkerName": "Z3 Carbonate Member",
                                            "MarkerMeasuredDepth": 3688.0
                                        },
                                        {
                                            "MarkerName": "Z2 Salt Member",
                                            "MarkerMeasuredDepth": 3709.0
                                        },
                                        {
                                            "MarkerName": "Z2 Basal Anhydrite Member",
                                            "MarkerMeasuredDepth": 3985.0
                                        },
                                        {
                                            "MarkerName": "Z2 Carbonate Member",
                                            "MarkerMeasuredDepth": 3996.0
                                        },
                                        {
                                            "MarkerName": "Z1 (Werra) Formation",
                                            "MarkerMeasuredDepth": 4022.5
                                        },
                                        {
                                            "MarkerName": "Ten Boer Member",
                                            "MarkerMeasuredDepth": 4070.0
                                        },
                                        {
                                            "MarkerName": "Upper Slochteren Member",
                                            "MarkerMeasuredDepth": 4128.5
                                        },
                                        {
                                            "MarkerName": "Ameland Member",
                                            "MarkerMeasuredDepth": 4231.0
                                        },
                                        {
                                            "MarkerName": "Lower Slochteren Member",
                                            "MarkerMeasuredDepth": 4283.5
                                        }
                                    ]
                                }
                            }
                        ],
                        "Datasets": []
                    }
                }
            }
        }
        headers = {
            'data-partition-id': f'{data_partition_id}',
            'Authorization': f'{token}',
            'subscription-key': f'{sub_key}'
            # 'Content-Type': 'application/json'
        }
        url = f"{adme_dns_host}/api/file/v2/files/{file_id}/metadata"
        response = requests.request(method="GET", url=url,
                                    headers=headers)
        response_json = response.json()
        print(f"{url=}")
        print(response)
        workflow_payload["executionContext"]["manifest"]["Data"]["Datasets"].append(response_json)
    return workflow_payload


if __name__ == "__main__":

    token = ""
    payload = get_workflow_payload("Osdu_Ingest",
                                   "default-qa-sis-internal-hq",
                                   "https://evt.api.enterprisedata.cloud.slb-ds.com",
                                   token,
                                   "2c4afa693efa4b679b7bf726b79d69dd",
                                   "default-qa-sis-internal-hq:dataset--File.Generic:5b718938-3635-4b6b-9d40-447ad5a816db",
                                   "Manifest.csv")
    print(payload)
