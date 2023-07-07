from sqlalchemy.orm import Session
from sqlalchemy import select, update
from fastapi import Depends
from utils import keygen, session_utils
from models import models
import schemas
from sqlalchemy import and_

URL = models.URL

get_session = session_utils.get_session


async def create_db_url(url: schemas.URLBase, db: Session = Depends(get_session)) -> URL:
    key = await keygen.create_unique_random_key(db)
    secret_key = f"{key}_{keygen.create_random_key(length=8)}"
    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    db.add(db_url)
    await db.commit()
    await db.refresh(db_url)
    return db_url


async def get_db_url_by_key(url_key: str, db: Session = Depends(get_session)) -> models.URL:
    statement = select(models.URL).where(
        and_(models.URL.key == url_key, models.URL.is_active))
    row = (await db.execute(statement)).first()
    return row


async def update_db_clicks(db: Session, db_url: schemas.URL) -> models.URL:
    stmt = (
        update(models.URL).
        where(models.URL.key == db_url[0].key).values(clicks=db_url[0].clicks + 1)
    )
    await db.execute(statement=stmt)
    await db.commit()
    return db_url
