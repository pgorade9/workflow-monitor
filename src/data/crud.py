from sqlalchemy.orm import Session

from src.data import schemas
from src.data import models


def create_corr_item(corr_item: schemas.correlationIds, db: Session):
    db_corr_item = models.CorrelationIds(env=corr_item.env, dag=corr_item.dag, corrId=corr_item.corrId,
                                         runId=corr_item.runId, fileId=corr_item.fileId)
    db.add(db_corr_item)
    db.commit()
    db.refresh(db_corr_item)
    return db_corr_item


def get_item(corr_id: str, db: Session):
    return db.query(models.CorrelationIds).filter(models.CorrelationIds.corrId == corr_id).first()
