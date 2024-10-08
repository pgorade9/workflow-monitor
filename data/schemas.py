from pydantic import BaseModel


class correlationIds(BaseModel):
    env: str
    dag: str
    corrId: str
    runId: str
    fileId: str


# class correlationIds(correlationIdsBase):
#     id: int
#
#     class Config:
#         from_attributes = True


class gsmRecords(BaseModel):
    env: str
    dag: str
    corrId: str
    recordId: str


# class gsmRecords(gsmRecordsBase):
#     id: int
#
#     class Config:
#         from_attributes = True
