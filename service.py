import asyncio
import json
import time
from typing import Optional, List
from retry import retry

import aiohttp
import requests
from pydantic import BaseModel
from sqlalchemy.orm import Session

from configuration import keyvault
from data import models




TIME_OUT = 60

def get_token(env):
    response = requests.request(method="POST",
                                url=keyvault[env]["token_url"],
                                headers={"content-type": "application/x-www-form-urlencoded"},
                                data=f"grant_type=client_credentials&client_id={keyvault[env]["client_id"]}&client_secret={keyvault[env]["client_secret"]}&scope={keyvault[env]["scope"]}")

    if response.status_code == 200:
        print(f"********* Token Generated Successfully ************")
        response_dict = json.loads(response.text)
        return "Bearer " + response_dict["access_token"]
    else:
        print(f"Error occurred while creating token. {response.text}")
        # exit(1)


def create_workflow_payload(env, dag):
    payload = {"executionContext": {}}
    payload["executionContext"]["dataPartitionId"] = keyvault[env]["data_partition_id"]
    payload["executionContext"]["id"] = keyvault[env]["file_id"][dag]
    return payload


async def trigger_workflow(session, env, dag_name, db):
    print("\nTriggering_workflow")

    workflow_url = f"{keyvault[env]["seds_dns_host"]}/api/workflow/v1/workflow/{dag_name}/workflowRun"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'data-partition-id': keyvault[env]["data_partition_id"],
        'Authorization': get_token(env)
    }
    payload = create_workflow_payload(env, dag_name)

    try:
        async with session.post(workflow_url, headers=headers, data=json.dumps(payload), timeout=TIME_OUT) as response:
            if response.status == 200:
                workflow_response_json = await response.json()
                workflow_response_json['correlation-id'] = response.headers['correlation-id']
                db_corr_item = models.CorrelationIds(env=env, dag=dag_name,
                                                     corrId=response.headers['correlation-id'],
                                                     runId=workflow_response_json['runId'],
                                                     fileId=keyvault[env]["file_id"][dag_name])
                db.add(db_corr_item)
                db.commit()
                db.refresh(db_corr_item)
                return workflow_response_json
            else:
                print(f"Bad Request {response.text}")
    except Exception as e:
        print(f"Error occurred while triggerring workflow for {env=} with {dag_name=}")
        print(f"Error: {e}")


async def async_workflow(envs, dags, db:Session):
    async with aiohttp.ClientSession() as aio_session:
        tasks = [trigger_workflow(aio_session, env, dag, db) for env in envs for dag in dags]
        start_time = int(time.time())

        await asyncio.gather(*tasks)
        end_time = int(time.time())
        net_time = end_time - start_time
        runs = len(db.query(models.CorrelationIds).all())

        db_time = db.query(models.TaskTimer).filter(models.TaskTimer.task == "TRIGGER_WORKFLOW").first()
        if db_time is not None:
            db_time.startTime = start_time
            db_time.endTime = end_time
            db_time.netTime = net_time
            db_time.runs = runs
        else:
            db_time = models.TaskTimer(task="TRIGGER_WORKFLOW", startTime=start_time, endTime=end_time,
                                       netTime=net_time,
                                       runs=runs)
        db.add(db_time)
        db.commit()
        db.refresh(db_time)

@retry(exceptions=Exception, tries=2, delay=1)
async def global_status(session, env, dag_name, correlation_Id, token, db: Session):
    print(f"Fetching status of {correlation_Id=} for {dag_name=} on {env=}")

    gsm_url = f"{keyvault[env]["seds_dns_host"]}/api/status-processor/v1/status/query"
    headers = {'data-partition-id': keyvault[env]["data_partition_id"],
               'Content-Type': 'application/json',
               'Authorization': token,
               'subscription-key': keyvault[env]["happy_me_subscription_key"]}
    payload = {"statusQuery": {}}
    payload["statusQuery"]["correlationId"] = correlation_Id

    try:
        async with session.post(gsm_url, headers=headers, data=json.dumps(payload),timeout=TIME_OUT) as response:
            response_json = await response.json()
            print(response.status)
            if response.status == 200:
                records = response_json["results"]
                gsm_records: List[GsmRecord] = [GsmRecord(**item) for item in records]

                for record in gsm_records:
                    if record.stage == "INGESTOR_SYNC" and record.status == "SUCCESS":
                        print(f"Record Stored Successfully : {record.recordId}")
                        item = db.query(models.GSMRecords).filter(models.GSMRecords.corrId == record.correlationId,
                                                                  models.GSMRecords.recordId == record.recordId).first()
                        if item is None:
                            db_stat_item = models.GSMRecords(env=env, dag=dag_name,
                                                             corrId=record.correlationId,
                                                             recordId=record.recordId, ingestorStatus="IN_PROGRESS")
                            db.add(db_stat_item)
                            db.commit()
                            db.refresh(db_stat_item)
                        else:
                            continue
                    elif record.stage in ["INGESTOR_SYNC", "INGESTOR"] and record.status == "FAILED":
                        print(f"Record Ingestion Failed : {record.message}")
                        item = db.query(models.GSMRecords).filter(
                            models.GSMRecords.corrId == record.correlationId).first()
                        if item is None:
                            db_stat_item = models.GSMRecords(env=env, dag=dag_name,
                                                             corrId=record.correlationId,
                                                             recordId="FAILED", ingestorStatus="FAILED")
                            db.add(db_stat_item)
                            db.commit()
                            db.refresh(db_stat_item)
                        else:
                            continue

                    if record.stage == "INGESTOR" and record.status == "SUCCESS":
                        record_items = db.query(models.GSMRecords).filter(
                            models.GSMRecords.corrId == record.correlationId).all()
                        for item in record_items:
                            print(f"Ingestor Success for {item.corrId=}")
                            item.ingestorStatus = "SUCCESS"
                            db.add(item)
                        db.commit()
            else:
                print(
                    f"correlationId: {payload["statusQuery"]["correlationId"]}: Response status code = {response.status} ")
                print("Please wait !!")
    except Exception as e:
        print(f"Error occurred while fetching GSM status for {payload["statusQuery"]["correlationId"]}")
        print(f"Error: {e}")


async def async_gsm(db):
    print("===================== Hey I was called by background task ======================")
    async with aiohttp.ClientSession() as aio_session:
        reference_set = [(item.env, item.dag, item.corrId) for item in db.query(models.CorrelationIds)]
        if len(reference_set)>0:
            relevant_set = []
            for item in reference_set:
                record = db.query(models.GSMRecords).filter(models.GSMRecords.corrId == item[2]).first()
                if record is None:
                    relevant_set.append(item)
                elif record.ingestorStatus == "IN_PROGRESS":
                    relevant_set.append(item)

            print(f"{relevant_set=}")
            envs = set([item[0] for item in relevant_set])
            token_map = {env: get_token(env) for env in envs}
            # start_time = int(time.time())
            await asyncio.gather(
                *[global_status(aio_session, run[0], run[1], run[2], token_map[run[0]], db) for run in relevant_set])
            # end_time = int(time.time())
            # net_time = end_time - start_time
            # db_time = models.TaskTimer(task="GSM_STATUS_QUERY", startTime=start_time, endTime=end_time, netTime=net_time,
            #                            runs=len(relevant_set))
            # db.add(db_time)
            # db.commit()
            # db.refresh(db_time)


async def workflow_status(session, env, dag_name, run_Id, token, db):
    print(f"Fetching Workflow status of {run_Id=} for {dag_name=} on {env=}")

    workflow_url = f"{keyvault[env]["seds_dns_host"]}/api/workflow/v1/workflow/{dag_name}/workflowRun/{run_Id}"
    headers = {'data-partition-id': keyvault[env]["data_partition_id"],
               'Content-Type': 'application/json',
               'Authorization': token,
               }
    try:
        async with session.get(workflow_url, headers=headers) as response:
            response_json = await response.json()
            print(response.status)
            if response.status == 200:
                workflowResponse: WorkflowResponse = WorkflowResponse(**response_json)
                record = db.query(models.WorkflowStatus).filter(models.WorkflowStatus.env == env,
                                                                models.WorkflowStatus.dag == dag_name).first()
                if record is None:
                    db_work_status_item = models.WorkflowStatus(env=env, dag=dag_name, status=workflowResponse.status)
                    db.add(db_work_status_item)
                    db.commit()
                    db.refresh(db_work_status_item)
                else:
                    record.status = workflowResponse.status
                    db.add(record)
                    db.commit()
                    db.refresh(record)

            else:
                print(f"Run-Id: {run_Id}: Response status code = {response.status} ")
                print("Please wait !!")
    except Exception as e:
        print(f"Error occurred while fetching WORKFLOW status for {run_Id}")
        print(f"Error: {e}")


async def async_workflow_status(db):
    runs = [(item.env, item.dag, item.runId) for item in db.query(models.CorrelationIds).all()]
    if len(runs) > 0:
        async with aiohttp.ClientSession() as aio_session:
            relevant_workflow_set = []
            for item in runs:
                record = db.query(models.WorkflowStatus).filter(models.WorkflowStatus.env == item[0],
                                                                models.WorkflowStatus.dag == item[1]).first()
                if record is None:
                    relevant_workflow_set.append(item)
                elif record.status in ["submitted","running"] :
                    relevant_workflow_set.append(item)
            print(f"{relevant_workflow_set=}")
            envs = set([run[0] for run in relevant_workflow_set])
            token_map = {env: get_token(env) for env in envs}
            # start_time = int(time.time())
            await asyncio.gather(
                *[workflow_status(aio_session, run[0], run[1], run[2], token_map[run[0]], db) for run in relevant_workflow_set])
            # end_time = int(time.time())
            # net_time = end_time - start_time
            # db_time = models.TaskTimer(task="WORKFLOW_STATUS_QUERY", startTime=start_time, endTime=end_time,
            #                            netTime=net_time,
            #                            runs=len(relevant_workflow_set))
            # db.add(db_time)
            # db.commit()
            # db.refresh(db_time)


class GsmRecord(BaseModel):
    correlationId: str
    recordId: Optional[str] = None
    recordIdVersion: Optional[str] = None
    stage: str
    status: str
    message: Optional[str] = None
    errorCode: int
    userEmail: str
    timestamp: int


class WorkflowResponse(BaseModel):
    workflowId: str
    runId: str
    startTimeStamp: int
    endTimeStamp: Optional[int] = None
    status: str
    submittedBy: str


if __name__ == "BatchRun":
    start_time = time.time()

    ######## Using Asyncio ###############
    # fp = open(CORRELATION_IDS_TXT, "w")
    # asyncio.run(async_workflow(fp))
    # fp.close()

    ######## Using Asyncio ###############
    # gp = open(GSM_STATUS_TXT, "w")
    # asyncio.run(async_gsm(gp))
    # gp.close()

    ####### ThreadPoolExecutor ###########
    # generate_uuid_thread(url)

    ####### ProcessPoolExecutor ###########
    # generate_uuid_process(url)

    end_time = time.time()
    print(f"Net Time = {end_time - start_time}")
