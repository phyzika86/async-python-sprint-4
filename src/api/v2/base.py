from fastapi import HTTPException, Depends, Request, UploadFile, APIRouter
from fastapi.responses import RedirectResponse
from src import schemas
import validators
from src.core.config import get_settings
from src.models import models

from sqlalchemy.orm import Session
from src.utils import crud, session_utils

from sqlalchemy import update

router = APIRouter()

app_settings = get_settings()
get_session = session_utils.get_session


async def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


async def raise_not_found(request):
    message = f"URL '{request.url}' не существует"
    raise HTTPException(status_code=404, detail=message)


async def raise_gone():
    message = f"Целевой ресурс больше недоступен на сервере происхождения"
    raise HTTPException(status_code=410, detail=message)


@router.get("/", description="Точка входа")
async def read_root():
    return "Добро пожаловать в сервис по созданию сокращенной формы передаваемых url"


@router.get('/get_status_db', description="Проверить статус подключения к БД")
async def get_status_db(db: Session = Depends(get_session)):
    try:
        await db.execute("""SELECT pg_database_size('collection') database_size""")
        res = 'Подключение к БД выполнено успешно'
    except Exception as e:
        res = f'Возникли проблемы с подключением к БД {e}'
    return res


@router.post("/url", response_model=schemas.URLInfo, description="Создать сокращенный url")
async def create_url(url: schemas.URLBase, db: Session = Depends(get_session)):
    if not validators.url(url.target_url):
        await raise_bad_request(message="Твой url является невалидным")

    db_url = await crud.create_db_url(db=db, url=url)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key

    return db_url


@router.delete("/delete/{url_key}", description="Удалить url по ключу")
async def delete_url(url_key: str, db: Session = Depends(get_session)):
    stmt = (
        update(models.URL).
        where(models.URL.key == url_key).
        values(is_delete=True)
    )

    await db.execute(statement=stmt)
    await db.commit()

    return 'Удаление URL c ключом  выполнено успешно'


@router.get("/{url_key}", description="Перейти на url по сокращенному ключу")
async def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_session)
):
    if db_url := await crud.get_db_url_by_key(db=db, url_key=url_key):
        if not db_url[0].is_delete:
            await crud.update_db_clicks(db=db, db_url=db_url)
            return RedirectResponse(db_url[0].target_url)

        await raise_gone()
    else:
        await raise_not_found(request)


@router.post("/file/upload-file")
async def butch_upload_file(file: UploadFile, db: Session = Depends(get_session)):
    urls = []
    for line in file.file:
        url = schemas.URLBase(target_url=line.decode('utf-8').rstrip())
        db_url = await create_url(url=url, db=db)
        res = {
            'url': db_url.target_url,
            'key': db_url.key
        }
        urls.append(res)
    return urls
