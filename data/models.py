from sqlalchemy import Column, Integer, String

from data.database import Base


class CorrelationIds(Base):
    __tablename__ = "correlationIds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    corrId = Column(String)
    runId = Column(String)
    fileId = Column(String)


class GSMRecords(Base):
    __tablename__ = "gsmRecords"
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    corrId = Column(String)
    recordId = Column(String)
    ingestorStatus = Column(String)


class WorkflowStatus(Base):
    __tablename__ = "workflowStatus"
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    status = Column(String)


class TaskTimer(Base):
    __tablename__ = "taskTimer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String)
    startTime = Column(Integer)
    endTime = Column(Integer)
    netTime = Column(Integer)
    runs = Column(Integer)