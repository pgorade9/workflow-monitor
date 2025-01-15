import asyncio
import csv

import pandas as pd
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.service.workflow_gsm_service import async_workflow, async_gsm, async_workflow_status
from src.constants.constants import DATA_SAMPLE
from configuration import keyvault

from src.data import models, schemas, crud
from src.data.database import engine, SessionLocal

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="excel_bin")
templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)
global setTimeOut, setEnvironments
setTimeOut = True
setEnvironments = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/correlationId", response_model=schemas.correlationIds)
def create(corr_entry: schemas.correlationIds, db: Session = Depends(get_db)):
    return crud.create_corr_item(corr_entry, db)


@app.get("/correlationId/{corr_id}", response_model=schemas.correlationIds)
def get_from_db(corr_id: str, db: Session = Depends(get_db)):
    db_corr_item = crud.get_item(corr_id, db)
    if not db_corr_item:
        raise HTTPException(status_code=404, detail="correlation Id NOT FOUND")
    return db_corr_item


@app.get("/")
def test():
    return {"Hello": 'world'}


@app.get("/get-corrIds")
def get_corr_Ids(db: Session = Depends(get_db)):
    envs = keyvault['envs-ltops']
    dags = keyvault['dags-ltops']
    correlationIds = {}

    for env in envs:
        correlationIds[env] = {}

        for dag in dags:
            corr_item = db.query(models.CorrelationIds).filter(models.CorrelationIds.env == env,
                                                               models.CorrelationIds.dag == dag).first()
            if corr_item is not None:
                correlationIds[env][dag] = corr_item.corrId

    return correlationIds


@app.get("/load-data", response_class=HTMLResponse)
def load_data(request: Request, db: Session = Depends(get_db)):
    db.query(models.CorrelationIds).delete()
    db.commit()
    with open(DATA_SAMPLE, "r") as fp:
        rows = csv.reader(fp)
        for row in rows:
            env, dag, corrId, runId, fileId = row[0], row[1], row[2], row[3], row[4]
            db_data = models.CorrelationIds(env=env, dag=dag, corrId=corrId, runId=runId, fileId=fileId)
            db.add(db_data)
            db.commit()
    return RedirectResponse("http://localhost:80/home")


@app.get("/write-data", response_class=HTMLResponse)
def write_data(request: Request, db: Session = Depends(get_db)):
    corr_objects = db.query(models.CorrelationIds)
    with open(DATA_SAMPLE, "w") as fp:
        for row in corr_objects:
            fp.write(f"{row.env},{row.dag},{row.corrId},{row.runId},{row.fileId}\n")
    return RedirectResponse("http://localhost:80/home")


def write_excel_workflows(db, envs, dags):
    data = {}
    for env in envs:
        data[env] = {}
        for dag in dags:
            item = db.query(models.CorrelationIds).filter(models.CorrelationIds.env == env,
                                                          models.CorrelationIds.dag == dag).first()
            if item is not None:
                data[env][dag] = item.corrId
            else:
                data[env][dag] = "-"
    df = pd.DataFrame(data)
    df.to_excel("output/workflowRun_correlationIds.xlsx")


def write_excel_runIds(db, envs, dags):
    data = {}
    for env in envs:
        data[env] = {}
        for dag in dags:
            item = db.query(models.CorrelationIds).filter(models.CorrelationIds.env == env,
                                                          models.CorrelationIds.dag == dag).first()
            if item is not None:
                data[env][dag] = item.runId
            else:
                data[env][dag] = "-"
    df = pd.DataFrame(data)
    df.to_excel("output/workflowRun_runIds.xlsx")


def write_excel_gsm(db, envs, dags):
    data = {}
    for env in envs:
        data[env] = {}
        for dag in dags:
            data[env][dag] = []
            items = db.query(models.GSMRecords).filter(models.GSMRecords.env == env, models.GSMRecords.dag == dag).all()
            if len(items) > 0:
                for item in items:
                    data[env][dag].append(item.recordId)
            else:
                data[env][dag] = "-"
    df = pd.DataFrame(data)
    df.to_excel("output/workflowRun_recordIds.xlsx")


@app.get("/home", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    if setEnvironments is None:
        envs = keyvault['envs-ltops']
        dags = keyvault['dags-ltops']
        first_entry = db.query(models.CorrelationIds).first()
        if first_entry is not None:
            if first_entry.env in keyvault['envs']:
                envs = keyvault['envs']
                dags = keyvault['dags']
    elif setEnvironments == 'ltops':
        envs = keyvault['envs-ltops']
        dags = keyvault['dags-ltops']
    else:
        envs = keyvault['envs']
        dags = keyvault['dags']

    correlationIds = {}
    runIds = {}
    workflow_status = {}
    gsm = {}

    for env in envs:
        correlationIds[env] = {}
        runIds[env] = {}
        workflow_status[env] = {}
        gsm[env] = {}

        for dag in dags:
            # Fetch Correlation Id
            corr_item = db.query(models.CorrelationIds).filter(models.CorrelationIds.env == env,
                                                               models.CorrelationIds.dag == dag).first()
            if corr_item is not None:
                correlationIds[env][dag] = corr_item.corrId

            # Fetch Run Id
            runId_item = db.query(models.CorrelationIds).filter(models.CorrelationIds.env == env,
                                                                models.CorrelationIds.dag == dag).first()
            if corr_item is not None:
                runIds[env][dag] = runId_item.runId

            # Fetch Workflow Status
            workflow_status_item = db.query(models.WorkflowStatus).filter(models.WorkflowStatus.env == env,
                                                                          models.WorkflowStatus.dag == dag).first()
            if workflow_status_item is not None:
                workflow_status[env][dag] = workflow_status_item.status

            # Fetch GSM status
            gsm_items = db.query(models.GSMRecords).filter(models.GSMRecords.env == env,
                                                           models.GSMRecords.dag == dag).all()
            if len(gsm_items) > 0:
                gsm[env][dag] = []
                for gsm_item in gsm_items:
                    gsm[env][dag].append(gsm_item.recordId)

    query_runs = db.query(models.TaskTimer).filter(models.TaskTimer.task == "TRIGGER_WORKFLOW").first()
    runs = query_runs.runs if query_runs is not None else 0
    query_netTime = db.query(models.TaskTimer).filter(models.TaskTimer.task == "TRIGGER_WORKFLOW").first()
    net_time = query_netTime.netTime if query_netTime is not None else 0

    tasks = BackgroundTasks()
    tasks.add_task(write_excel_workflows, db, envs, dags)
    tasks.add_task(write_excel_gsm, db, envs, dags)
    tasks.add_task(write_excel_runIds, db, envs, dags)

    return templates.TemplateResponse(name="index.html", request=request,
                                      context={'result': correlationIds, 'runIds': runIds, 'gsm': gsm,
                                               'workflow_status': workflow_status,
                                               'envs': envs, 'dags': dags, 'runs': runs,
                                               'net_time': net_time, 'setTimeOut': setTimeOut}, background=tasks)


@app.get("/clear")
async def clear_db(db: Session = Depends(get_db)):
    print("Clearing All database........")
    stop_update()
    db.query(models.CorrelationIds).delete(synchronize_session=False)
    db.query(models.GSMRecords).delete(synchronize_session=False)
    db.query(models.WorkflowStatus).delete(synchronize_session=False)
    db.query(models.TaskTimer).delete(synchronize_session=False)
    db.commit()
    return RedirectResponse("http://localhost:80/home")


@app.get("/update")
def update(db: Session = Depends(get_db)):
    print(f"Checking for Updates...............")
    tasks = BackgroundTasks()
    tasks.add_task(async_workflow_status, db)
    tasks.add_task(async_gsm, db)
    return RedirectResponse("http://localhost:80/home", background=tasks)


@app.get("/stop-update")
def stop_update(db: Session = Depends(get_db)):
    print(f"Stopping all Updates...............")
    global setTimeOut
    setTimeOut = False
    return RedirectResponse("http://localhost:80/home")


@app.get("/trigger/workflow/saas")
def trigger_workflow_saas(db: Session = Depends(get_db)):
    clear_db()
    envs = keyvault['envs']
    dags = keyvault['dags']

    global setTimeOut
    setTimeOut = True

    tasks = BackgroundTasks()
    tasks.add_task(setEnvironmentsFunc, 'saas')
    tasks.add_task(trigger_workflow, dags, envs, db)
    tasks.add_task(write_excel_workflows, db, envs, dags)

    return RedirectResponse("http://localhost:80/home", background=tasks)


@app.get("/trigger/workflow/ltops")
def trigger_workflow_ltops(db: Session = Depends(get_db)):
    clear_db()
    envs = keyvault['envs-ltops']
    dags = keyvault['dags-ltops']

    global setTimeOut
    setTimeOut = True

    tasks = BackgroundTasks()
    tasks.add_task(setEnvironmentsFunc, 'ltops')
    tasks.add_task(trigger_workflow, dags, envs, db)
    tasks.add_task(write_excel_workflows, db, envs, dags)

    return RedirectResponse("http://localhost:80/home", background=tasks)


def setEnvironmentsFunc(value: str):
    global setEnvironments
    setEnvironments = value


def trigger_workflow(dags, envs, db):
    asyncio.run(async_workflow(envs, dags, db))


if __name__ == "__main__":
    uvicorn.run('app:app', port=80, host="127.0.0.1", reload=True)
