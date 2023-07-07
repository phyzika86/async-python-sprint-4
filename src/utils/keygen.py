import secrets
import string
from utils import session_utils
from fastapi import Depends

from sqlalchemy.orm import Session

from utils import crud

get_session = session_utils.get_session


def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def create_unique_random_key(db: Session = Depends(get_session)) -> str:
    key = create_random_key()
    while await crud.get_db_url_by_key(db=db, url_key=key):
        key = create_random_key()
    return key
