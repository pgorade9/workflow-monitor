from sqlalchemy import Column, Integer, String

from src.data.database import Base


class CorrelationIds(Base):
    __tablename__ = "correlationIds"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    corrId = Column(String)
    runId = Column(String)
    fileId = Column(String)


class GSMRecords(Base):
    __tablename__ = "gsmRecords"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    corrId = Column(String)
    recordId = Column(String)
    ingestorStatus = Column(String)


class WorkflowStatus(Base):
    __tablename__ = "workflowStatus"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    env = Column(String)
    dag = Column(String)
    status = Column(String)


class TaskTimer(Base):
    __tablename__ = "taskTimer"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    task = Column(String)
    startTime = Column(Integer)
    endTime = Column(Integer)
    netTime = Column(Integer)
    runs = Column(Integer)